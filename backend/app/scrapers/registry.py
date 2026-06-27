from app.scrapers.base import BaseSourceAdapter
from app.scrapers.doq import DoqAdapter
from app.scrapers.helix import HelixAdapter
from app.scrapers.invitro import InvitroAdapter
from app.scrapers.kdl_olymp import KdlOlympAdapter

_ADAPTERS: dict[str, type[BaseSourceAdapter]] = {
    "kdl_olymp": KdlOlympAdapter,
    "doq": DoqAdapter,
    "invitro": InvitroAdapter,
    "helix": HelixAdapter,
}


def available_sources() -> list[str]:
    return list(_ADAPTERS)


def get_adapter(source_name: str) -> BaseSourceAdapter:
    try:
        return _ADAPTERS[source_name]()
    except KeyError:
        raise ValueError(f"Unknown source: {source_name}") from None
