from typing import Literal

import bcrypt


def hash_password(password: str, algo: Literal["bcrypt"] = "bcrypt") -> str:
    if algo == "bcrypt":
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    else:
        raise NotImplementedError(algo)


def validate_password(
    password: str, hash: str, algo: Literal["bcrypt"] = "bcrypt"
) -> bool:
    if algo == "bcrypt":
        return bcrypt.checkpw(password.encode(), hash.encode())
    else:
        raise NotImplementedError(algo)
