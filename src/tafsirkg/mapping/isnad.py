"""Builds narrator chains (isnads) from the ``<persName>`` elements of a hadith paragraph.

Rules:

* Narrators are the ``<persName>`` elements of the paragraph in document order,
  excluding any inside the matn (``<said>``) or a quotation.
* A chain starts at each ``shaykh`` (Tabari's own teacher), so a paragraph that cites
  several isnads ("... وحدثنا ...") yields several chains.
* Narrators named before the first ``shaykh`` are not part of a chain (the report is
  told first and its isnad given afterwards); they become person mentions.
* The last narrator of each chain is its root narrator.
* Consecutive narrators are linked with ``heardFrom`` by the RDF layer. Chains naming
  more than one Companion may branch ("وعن ..."), which a linear chain cannot express;
  they are reported for review.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass, field

from tafsirkg.domain.model import ChainLink, Hadith, NarratorChain, NarratorRole
from tafsirkg.issues import IssueCode, IssueLog
from tafsirkg.mapping import identity
from tafsirkg.mapping.registry import EntityRegistry
from tafsirkg.tei import model as tei
from tafsirkg.tei.text import plain_text

_ROLE_SEPARATORS = re.compile(r"[\s,]+")
_COMPANION_ROLES = frozenset({NarratorRole.SAHABI.value, NarratorRole.UNKNOWN_SAHABI.value})
_KNOWN_ROLES = {role.value: role for role in NarratorRole}


@dataclass
class IsnadResult:
    """Which ``<persName>`` nodes (by ``id()``) became chain links or plain mentions."""

    in_chain: set[int] = field(default_factory=set)
    mentioned_only: set[int] = field(default_factory=set)


def _role_tokens(name: tei.PersName) -> tuple[str, ...]:
    return tuple(token.lower() for token in _ROLE_SEPARATORS.split(name.ana or "") if token)


def _is_shaykh(name: tei.PersName) -> bool:
    return NarratorRole.SHAYKH.value in _role_tokens(name)


def _isnad_names(element: tei.TeiElement) -> Iterator[tei.PersName]:
    for child in element.elements():
        if isinstance(child, tei.PersName):
            yield child
        elif not isinstance(child, (tei.Said, tei.Quote)):
            yield from _isnad_names(child)


class IsnadBuilder:
    def __init__(self, registry: EntityRegistry, issues: IssueLog) -> None:
        self._registry = registry
        self._issues = issues

    def build(self, hadith: Hadith, paragraph: tei.Paragraph) -> IsnadResult:
        result = IsnadResult()
        names = list(_isnad_names(paragraph))
        if not names:
            self._issues.warning(
                IssueCode.HADITH_WITHOUT_CHAIN, f"{hadith.id} has no <persName>", paragraph.source
            )
            return result

        groups = self._split_at_shaykh(names)
        if any(_is_shaykh(name) for name in names) and not _is_shaykh(groups[0][0]):
            leading = groups.pop(0)
            result.mentioned_only.update(id(name) for name in leading)
            self._issues.warning(
                IssueCode.NARRATOR_BEFORE_CHAIN,
                f"{hadith.id}: {[plain_text(name) for name in leading]} named before the first "
                "shaykh; kept as person mentions, not as chain links",
                leading[0].source,
            )
        elif not _is_shaykh(groups[0][0]):
            self._issues.warning(
                IssueCode.CHAIN_WITHOUT_SHAYKH,
                f"{hadith.id}: chain does not start with a shaykh",
                groups[0][0].source,
            )

        for index, group in enumerate(groups, start=1):
            hadith.chains.append(self._chain(identity.chain(hadith.id, index), group))
            result.in_chain.update(id(name) for name in group)
        return result

    @staticmethod
    def _split_at_shaykh(names: list[tei.PersName]) -> list[list[tei.PersName]]:
        groups: list[list[tei.PersName]] = [[]]
        for name in names:
            if _is_shaykh(name) and groups[-1]:
                groups.append([])
            groups[-1].append(name)
        return groups

    def _chain(self, chain_id: str, names: list[tei.PersName]) -> NarratorChain:
        chain = NarratorChain(chain_id)
        for position, name in enumerate(names, start=1):
            chain.links.append(self._link(identity.chain_link(chain_id, position), position, name))
        chain.root.narrator.is_root = True

        companions = [link for link in chain.links if _COMPANION_ROLES.intersection(link.role_tokens)]
        if len(companions) > 1:
            self._issues.warning(
                IssueCode.POSSIBLE_BRANCHING_CHAIN,
                f"{chain_id} names {len(companions)} companions; the isnad may branch",
                names[0].source,
            )
        return chain

    def _link(self, link_id: str, position: int, name: tei.PersName) -> ChainLink:
        tokens = _role_tokens(name)
        narrator_id = name.n.strip() if name.n and name.n.strip() else None
        narrator = self._registry.narrator(narrator_id, plain_text(name), link_id)
        if narrator_id is None:
            self._issues.info(
                IssueCode.NARRATOR_WITHOUT_ID,
                f"narrator {plain_text(name)!r} has no ID; kept as a separate narrator",
                name.source,
            )
        for token in tokens:
            if token in _KNOWN_ROLES:
                narrator.roles.add(_KNOWN_ROLES[token])
            else:
                self._issues.warning(
                    IssueCode.UNKNOWN_NARRATOR_ROLE,
                    f"role {token!r} of {plain_text(name)!r} is not a NarratorType; "
                    "kept on the chain link only",
                    name.source,
                )
        return ChainLink(link_id, position, narrator, tokens)
