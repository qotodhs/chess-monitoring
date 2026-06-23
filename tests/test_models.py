from chess_monitoring.models import MeasurementRecord, fan_law_power_ratio


def test_fan_law_power_ratio():
    assert fan_law_power_ratio(70) == 0.343
    assert fan_law_power_ratio(85) == 0.614125


def test_record_from_payload():
    record = MeasurementRecord.from_payload(
        site_id="SITE-A",
        ahu_id="AHU-01",
        payload={"co2_ppm": 700, "fan_speed_pct": 70, "power_kw": 12.3},
    )

    assert record.site_id == "SITE-A"
    assert record.ahu_id == "AHU-01"
    assert record.to_dict()["fan_law_power_ratio"] == 0.343
