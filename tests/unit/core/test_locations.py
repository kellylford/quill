from quill.core.locations import LocationRing


def test_location_ring_back_and_forward() -> None:
    ring = LocationRing()
    ring.record(10)
    ring.record(25)
    ring.record(40)

    assert ring.back(40) == 25
    assert ring.back(25) == 10
    assert ring.back(10) is None
    assert ring.forward(10) == 25
    assert ring.forward(25) == 40
    assert ring.forward(40) is None


def test_location_ring_drops_forward_history_when_recording_new_position() -> None:
    ring = LocationRing()
    ring.record(1)
    ring.record(2)
    ring.record(3)
    assert ring.back(3) == 2
    ring.record(50)
    assert ring.forward(50) is None
