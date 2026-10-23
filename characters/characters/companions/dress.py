"""A Lemmy just born dressed as a hunter, so that the hunter companions are Lemmy in a hunter's look (decision 18 of
docs/renforts/README.md), at each birth: a Lemmy coming back after his death is a new character, born himself
(trial 189, vérifié en jeu), and is dressed again here.

The steps of docs/renforts/sondes/run_renforts_wear.py for a Lemmy still himself (trials 156 to 159 and 189,
vérifié en jeu): his own mesh draws the hunter's upper body, each of the hunter's other parts is hung on it, then
every mesh drawing the hunter is given its model's own materials. A Lemmy whose mesh is not his own as trial 152
read it, or who wears a hunter already, is left as he is. Nothing is done until every part is loaded and every call
has the parameters expected.

In two steps (Dressing), since trial 190: the probes dressed him from the console, and his mesh drew the upper body at
once; It Follows dresses him from its hook on the animation update, and his mesh read his own model right after the
call, then the hunter's a while later (vérifié en jeu, six times out of six). Dressed in one go, the rest stopped
there and his mesh was left drawing the upper body alone, unpainted: pieces floating. So start() gives the upper body,
and step() hangs the rest once the game draws it, or gives up after WAIT_S, nothing more done.

Hidden meanwhile (Kevin, 2026-10-21: « on les voit sous l'apparence de Lemmy pendant une seconde et ensuite on les
voit changer c'est vraiment pas propre »): the whole character, by the actor's own flag, which leaves each part's
own visibility as the game set it; shown again whatever the outcome, so that a companion never stays invisible.

When the player chose his own colours for that hunter (the outfit his mod gives, tuning.py; player_paint.py), they are
put over the hunter's own materials last, on the slots they fit; none fitting (the player plays another hunter) leaves
the hunter's own.
His head, read with them before anything is done, takes the base head's place (player_paint.headed); a head that
cannot be loaded leaves the base one rather than no dressing at all.
"""

from typing import Any, Callable

from . import hunters, player_paint, wear

BODY = "CharacterMesh"
SKELETON = "SK_GunToter_Skeleton"
# The trials' bound on the slots painted (paint_reads.MAX_SLOTS); a slot past it would keep its old material.
MAX_SLOTS = 24
# How long the game may take to draw the upper body before the dressing gives up (non vérifié: a frame or two
# expected).
WAIT_S = 3.0
MAX_TEXT = 120


def _failed(step: str, error: Exception) -> dict:
    return {"done": f"{step}_failed", "error": f"{type(error).__name__}:{str(error)[:MAX_TEXT]}"}


def ready(actor: Any, name: str, head: str | None = None) -> tuple[Any, Any, dict] | dict:
    """His mesh, the look (with the player's head when it fits) and its models, once he is himself, every call holds
    and every part is loaded; else why not, nothing done."""
    look = hunters.BY_NAME.get(name)
    if look is None:
        return {"done": "no_look"}
    look = player_paint.headed(look, head)
    body = actor.Mesh
    model = wear.model_of(body)
    skeleton = str(model.Skeleton.Name) if model is not None else None
    if hunters.wearing(wear.drawing(body)) is not None:
        return {"done": "dressed_already"}
    if str(body.Name) != BODY or skeleton != SKELETON:
        return {"done": "not_himself", "mesh": str(body.Name), "skeleton": skeleton}
    differ = wear.differing()
    if differ:
        return {"done": "calls_differ", "calls": differ}
    models = {path: wear.load(path) for path in (look.upper, *look.followers)}
    missing = [path.rsplit(".", 1)[-1] for path, found in models.items() if found is None]
    if missing:
        return {"done": "not_loaded", "parts": missing}
    return body, look, models


class Dressing:
    """One Lemmy being dressed as the hunter of that name: actor his weak pointer, clock() the team's time;
    own() what the player wears (player_paint.Own) when he is to wear it, None for the hunter's own."""

    def __init__(self, actor: Callable[[], Any], name: str, clock: Callable[[], float],
                 own: Callable[[], Any] | None = None) -> None:
        self.actor, self.name, self.clock, self.own = actor, name, clock, own
        self.found: tuple | None = None
        self.since = 0.0
        self.player: Any = None
        self.unread: str | None = None

    def start(self) -> dict:
        """Hidden, then given the upper body: swapped, or why not, shown and nothing more done."""
        actor = self.actor()
        if actor is None:
            return {"done": "gone"}
        self._read_player()
        head = None if self.player is None else self.player.head
        found = ready(actor, self.name, head)
        if head is not None and isinstance(found, dict) and found["done"] == "not_loaded":
            found = ready(actor, self.name)
        if isinstance(found, dict):
            return found
        body, look, models = found
        try:
            wear.hide(actor, True)
        except Exception as error:
            return _failed("hide", error)
        try:
            wear.draw(body, models[look.upper])
        except Exception as error:
            return self._shown(actor, _failed("swap", error))
        self.found, self.since = found, self.clock()
        return {"done": "swapped", "hunter": look.name}

    def step(self) -> dict | None:
        """None while the game does not draw the upper body yet; else the outcome, the hunter shown again."""
        actor = self.actor()
        if actor is None or self.found is None:
            return {"done": "gone"}
        body, look, models = self.found
        waited = round(self.clock() - self.since, 2)
        if not hunters.same(wear.drawing(body), look.upper):
            if waited < WAIT_S:
                return None
            return self._shown(actor, {"done": "swap_not_taken", "waited_s": waited})
        return self._shown(actor, {**self._rest(actor, body, look, models), "waited_s": waited})

    def give_up(self) -> None:
        """The team stops before he is dressed: shown again as he is."""
        actor = self.actor()
        if actor is not None:
            self._shown(actor, {})

    def _rest(self, actor: Any, body: Any, look: Any, models: dict) -> dict:
        drawn, placed = [(body, look.upper)], wear.identity()
        for path in look.followers:
            try:
                drawn.append((wear.wear(actor, body, models[path], placed), path))
            except Exception as error:
                return _failed("wear", error)
        try:
            slots = sum(wear.repaint(mesh, models[path], MAX_SLOTS) for mesh, path in drawn)
        except Exception as error:
            return _failed("paint", error)
        worn = {"done": "worn", "hunter": look.name, "hung": len(look.followers), "slots": slots}
        if self.own is None:
            return worn
        if self.player is None:
            return {**worn, "player": self.unread}
        try:
            worn["player"] = player_paint.paint([(mesh, models[path]) for mesh, path in drawn], self.player.paints)
        except Exception as error:
            return {**worn, "player": _failed("player", error)["error"]}
        base = hunters.BY_NAME[look.name].followers
        worn["player_paints"] = len(self.player.paints)
        worn["player_head"] = next((part.rsplit(".", 1)[-1] for part in look.followers if part not in base), None)
        if worn["player_head"] is None:
            worn["player_parts"] = list(self.player.parts)
        return worn

    def _read_player(self) -> None:
        """What the player wears, read once before he is dressed; unread: said, his own outfit worn."""
        if self.own is None:
            return
        try:
            self.player = self.own()
        except Exception as error:
            self.unread = _failed("player", error)["error"]

    @staticmethod
    def _shown(actor: Any, outcome: dict) -> dict:
        try:
            wear.hide(actor, False)
        except Exception as error:
            return {**outcome, "shown": f"failed:{type(error).__name__}"}
        return outcome
