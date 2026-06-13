from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "config" / "droid-config.sh"

def _parse_simple_shell_exports(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


@dataclass(frozen=True)
class DroidConfig:
    raw: dict[str, str]

    @property
    def droid_address(self) -> str:
        return self.raw["DROID_ADDRESS"]

    @property
    def adb_port(self) -> int:
        return int(self.raw["ADB_PORT"])

    @property
    def ssh_port(self) -> int:
        return int(self.raw["SSH_PORT"])

    @property
    def ssh_user(self) -> str:
        return self.raw["SSH_USER"]

    @property
    def termux_shell_helper_root(self) -> Path:
        return Path(self.raw["TERMUX_SHELL_HELPER_ROOT"]).expanduser()

    @property
    def remote_workdir(self) -> Path:
        return Path(self.raw["REMOTE_WORKDIR"])

    @property
    def esde_root(self) -> Path:
        return Path(self.raw["ESDE_ROOT"])

    @property
    def esde_custom_systems_dir(self) -> Path:
        return self.esde_root / "custom_systems"

    @property
    def retroarch_dir(self) -> Path:
        return Path(self.raw["RETROARCH_DIR"])

    @property
    def retroarch_system_dir(self) -> Path:
        return self.retroarch_dir / self.raw["RETROARCH_SUBDIR_SYSTEM"]

    @property
    def retroarch_cores_dir(self) -> Path:
        return self.retroarch_dir / self.raw["RETROARCH_SUBDIR_CORES"]

    @property
    def retroarch_info_dir(self) -> Path:
        return self.retroarch_dir / self.raw["RETROARCH_SUBDIR_INFO"]

    @property
    def retro_games_dir(self) -> Path:
        return Path(self.raw["RETRO_GAMES_DIR"])

    @property
    def roms_root(self) -> Path:
        return self.retro_games_dir / "roms"

    @property
    def bios_root(self) -> Path:
        return self.retro_games_dir / "bios"

    @property
    def installers_root(self) -> Path:
        return self.retro_games_dir / "installers"



@lru_cache(maxsize=1)
def load_droid_config() -> DroidConfig:
    return DroidConfig(_parse_simple_shell_exports(CONFIG_PATH))
