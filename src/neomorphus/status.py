from dataclasses import dataclass


@dataclass(frozen=True)
class Stage:
    name: str

    def __str__(self) -> str:
        return self.name

    def __format__(self, format_spec: str) -> str:
        return format(self.name, format_spec)
