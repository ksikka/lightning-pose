import typing

SessionKey: typing.TypeAlias = str
LabelFileKey: typing.TypeAlias = str
ViewName: typing.TypeAlias = str

class VideoFileKey(typing.NamedTuple):
    session_key: SessionKey
    view: ViewName | None = None

class VideoFrameKey(typing.NamedTuple):
    session_key: str
    frame_index: int
    view: ViewName | None = None

