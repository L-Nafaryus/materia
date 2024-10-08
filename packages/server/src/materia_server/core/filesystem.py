from typing import Optional, Self, Iterator, TypeVar
from pathlib import Path
import aiofiles
from aiofiles import os as async_os
from aiofiles import ospath as async_path
import aioshutil
import re
from tempfile import NamedTemporaryFile
from streaming_form_data.targets import BaseTarget
from uuid import uuid4
from materia_server.core.misc import optional


valid_path = re.compile(r"^/(.*/)*([^/]*)$")


class FileSystemError(Exception):
    pass


class FileSystem:
    def __init__(self, path: Path, isolated_directory: Optional[Path] = None):
        if path == Path() or path is None:
            raise FileSystemError("The given path is empty")

        self.path = path

        if isolated_directory and not isolated_directory.is_absolute():
            raise FileSystemError("The isolated directory must be absolute")

        self.isolated_directory = isolated_directory
        # self.working_directory = working_directory
        # self.relative_path = path.relative_to(working_directory)

    async def exists(self) -> bool:
        return await async_path.exists(self.path)

    async def size(self) -> int:
        return await async_path.getsize(self.path)

    async def is_file(self) -> bool:
        return await async_path.isfile(self.path)

    async def is_directory(self) -> bool:
        return await async_path.isdir(self.path)

    def name(self) -> str:
        return self.path.name

    async def check_isolation(self, path: Path):
        if not self.isolated_directory:
            return
        if not (await async_path.exists(self.isolated_directory)):
            raise FileSystemError("Missed isolated directory")
        if not optional(path.relative_to, self.isolated_directory):
            raise FileSystemError(
                "Attempting to work with a path that is outside the isolated directory"
            )
        if self.path == self.isolated_directory:
            raise FileSystemError("Attempting to modify the isolated directory")

    async def remove(self, shallow: bool = False):
        await self.check_isolation(self.path)
        try:
            if await self.exists() and await self.is_file() and not shallow:
                await aiofiles.os.remove(self.path)

            if await self.exists() and await self.is_directory() and not shallow:
                await aioshutil.rmtree(str(self.path))
        except OSError as e:
            raise FileSystemError(*e.args) from e

    async def generate_name(self, target_directory: Path, name: str) -> str:
        """Generate name based on target directory contents and self type."""
        count = 1
        new_path = target_directory.joinpath(name)

        while await async_path.exists(new_path):
            if await self.is_file():
                if with_counter := re.match(r"^(.+)\.(\d+)\.(\w+)$", new_path.name):
                    new_name, _, extension = with_counter.groups()
                elif with_extension := re.match(r"^(.+)\.(\w+)$", new_path.name):
                    new_name, extension = with_extension.groups()

                new_path = target_directory.joinpath(
                    "{}.{}.{}".format(new_name, count, extension)
                )

            if await self.is_directory():
                if with_counter := re.match(r"^(.+)\.(\d+)$", new_path.name):
                    new_name, _ = with_counter.groups()
                else:
                    new_name = new_path.name

                new_path = target_directory.joinpath("{}.{}".format(new_name, count))

            count += 1

        return new_path.name

    async def _generate_new_path(
        self,
        target_directory: Path,
        new_name: Optional[str] = None,
        force: bool = False,
        shallow: bool = False,
    ) -> Path:
        new_name = new_name or self.path.name

        if await async_path.exists(target_directory.joinpath(new_name)):
            if force or shallow:
                new_name = await self.generate_name(target_directory, new_name)
            else:
                raise FileSystemError("Target destination already exists")

        return target_directory.joinpath(new_name)

    async def move(
        self,
        target_directory: Path,
        new_name: Optional[str] = None,
        force: bool = False,
        shallow: bool = False,
    ) -> Self:
        await self.check_isolation(self.path)
        new_path = await self._generate_new_path(
            target_directory, new_name, force=force, shallow=shallow
        )
        target = FileSystem(new_path, self.isolated_directory)

        try:
            if await self.exists() and not shallow:
                await aioshutil.move(self.path, new_path)
        except Exception as e:
            raise FileSystemError(*e.args) from e

        return target

    async def rename(
        self, new_name: str, force: bool = False, shallow: bool = False
    ) -> Self:
        return await self.move(
            self.path.parent, new_name=new_name, force=force, shallow=shallow
        )

    async def copy(
        self,
        target_directory: Path,
        new_name: Optional[str] = None,
        force: bool = False,
        shallow: bool = False,
    ) -> Self:
        await self.check_isolation(self.path)
        new_path = await self._generate_new_path(
            target_directory, new_name, force=force, shallow=shallow
        )
        target = FileSystem(new_path, self.isolated_directory)

        try:
            if await self.is_file() and not shallow:
                await aioshutil.copy(self.path, new_path)

            if await self.is_directory() and not shallow:
                await aioshutil.copytree(self.path, new_path)
        except Exception as e:
            raise FileSystemError(*e.args) from e

        return target

    async def make_directory(self, force: bool = False):
        try:
            if await self.exists() and not force:
                raise FileSystemError("Already exists")

            await async_os.makedirs(self.path, exist_ok=force)
        except Exception as e:
            raise FileSystemError(*e.args)

    async def write_file(self, data: bytes, force: bool = False):
        try:
            if await self.exists() and not force:
                raise FileSystemError("Already exists")

            async with aiofiles.open(self.path, mode="wb") as file:
                await file.write(data)
        except Exception as e:
            raise FileSystemError(*e.args)

    @staticmethod
    def check_path(path: Path) -> bool:
        return bool(valid_path.match(str(path)))

    @staticmethod
    def normalize(path: Path) -> Path:
        """Resolve path and make it relative."""
        if not path.is_absolute():
            path = Path("/").joinpath(path)

        return Path(*path.resolve().parts[1:])


class TemporaryFileTarget(BaseTarget):
    def __init__(
        self, working_directory: Path, allow_overwrite: bool = True, *args, **kwargs
    ):
        if working_directory == Path():
            raise FileSystemError("The given working directory is empty")

        super().__init__(*args, **kwargs)

        self._mode = "wb" if allow_overwrite else "xb"
        self._fd = None
        self._path = working_directory.joinpath("cache", str(uuid4()))

    def on_start(self):
        if not self._path.parent.exists():
            self._path.parent.mkdir(exist_ok=True)

        self._fd = open(str(self._path), mode="wb")

    def on_data_received(self, chunk: bytes):
        if self._fd:
            self._fd.write(chunk)

    def on_finish(self):
        if self._fd:
            self._fd.close()

    def path(self) -> Optional[Path]:
        return self._path

    def remove(self):
        if self._fd:
            if (path := Path(self._fd.name)).exists():
                path.unlink()
