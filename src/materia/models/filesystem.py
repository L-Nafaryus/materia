from typing import Optional, Self, Iterator, TypeVar
from pathlib import Path
import aiofiles
from aiofiles import os as async_os
from aiofiles import ospath as async_path
import aioshutil
import re

valid_path = re.compile(r"^/(.*/)*([^/]*)$")


class FileSystemError(Exception):
    pass


T = TypeVar("T")


def wrapped_next(i: Iterator[T]) -> Optional[T]:
    try:
        return next(i)
    except StopIteration:
        return None


class FileSystem:
    def __init__(self, path: Path, working_directory: Path):
        if path == Path():
            raise FileSystemError("The given path is empty")
        if working_directory == Path():
            raise FileSystemError("The given working directory is empty")

        self.path = path
        self.working_directory = working_directory
        self.relative_path = path.relative_to(working_directory)

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

    async def remove(self):
        try:
            if await self.is_file():
                await aiofiles.os.remove(self.path)

            if await self.is_directory():
                await aioshutil.rmtree(str(self.path))

        except OSError as e:
            raise FileSystemError(
                f"Failed to remove content at /{self.relative_path}:",
                *e.args,
            )

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
        if self.path == self.working_directory:
            raise FileSystemError("Cannot modify working directory")

        new_name = new_name or self.path.name

        if await async_path.exists(target_directory.joinpath(new_name)) and not shallow:
            if force:
                new_name = await self.generate_name(target_directory, new_name)
            else:
                raise FileSystemError(
                    f"Target destination already exists /{target_directory.joinpath(new_name)}"
                )

        return target_directory.joinpath(new_name)

    async def move(
        self,
        target_directory: Path,
        new_name: Optional[str] = None,
        force: bool = False,
        shallow: bool = False,
    ):
        new_path = await self._generate_new_path(
            target_directory, new_name, force=force, shallow=shallow
        )

        try:
            if not shallow:
                await aioshutil.move(self.path, new_path)

        except Exception as e:
            raise FileSystemError(
                f"Failed to move content from /{self.relative_path}:",
                *e.args,
            )

        return FileSystem(new_path, self.working_directory)

    async def rename(
        self, new_name: str, force: bool = False, shallow: bool = False
    ) -> Path:
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
        new_path = await self._generate_new_path(
            target_directory, new_name, force=force, shallow=shallow
        )

        try:
            if not shallow:
                if await self.is_file():
                    await aioshutil.copy(self.path, new_path)

                if await self.is_directory():
                    await aioshutil.copytree(self.path, new_path)

        except Exception as e:
            raise FileSystemError(
                f"Failed to copy content from /{new_path}:",
                *e.args,
            )

        return FileSystem(new_path, self.working_directory)

    async def make_directory(self):
        try:
            if await self.exists():
                raise FileSystemError("Failed to create directory: already exists")

            await async_os.mkdir(self.path)
        except Exception as e:
            raise FileSystemError(
                f"Failed to create directory at /{self.relative_path}:",
                *e.args,
            )

    async def write_file(self, data: bytes):
        try:
            if await self.exists():
                raise FileSystemError("Failed to write file: already exists")

            async with aiofiles.open(self.path, mode="wb") as file:
                await file.write(data)
        except Exception as e:
            raise FileSystemError(
                f"Failed to write file to /{self.relative_path}:",
                *e.args,
            )

    @staticmethod
    def check_path(path: Path) -> bool:
        return bool(valid_path.match(str(path)))

    @staticmethod
    def normalize(path: Path) -> Path:
        """Resolve path and make it relative."""
        if not path.is_absolute():
            path = Path("/").joinpath(path)

        return Path(*path.resolve().parts[1:])
