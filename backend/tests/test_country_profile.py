from app.core.country import get_country_profile
from app.modules.facilities.routes import _sync_country_geography


def test_guinea_profile_is_default():
    profile = get_country_profile("GN")
    assert profile.code == "GN"
    assert profile.currency_code == "GNF"
    assert profile.phone_country_code == "+224"
    assert profile.timezone == "Africa/Conakry"
    assert "DHIS2_SISR" in profile.national_integrations
    assert "E_SIGL" in profile.national_integrations
    assert "IHRIS" in profile.national_integrations


def test_unknown_country_gets_generic_profile():
    profile = get_country_profile("ZZ")
    assert profile.code == "ZZ"
    assert profile.administrative_levels[0].key == "admin_level_1"
    assert profile.health_system_levels[-1].key == "community"


def test_guinea_legacy_geography_is_mirrored_to_generic_levels():
    data = _sync_country_geography(
        {
            "country_code": "GN",
            "region": "Conakry",
            "prefecture": "Conakry",
            "commune": "Ratoma",
        }
    )
    assert data["admin_level_1"] == "Conakry"
    assert data["admin_level_2"] == "Conakry"
    assert data["admin_level_3"] == "Ratoma"


def test_guinea_generic_levels_are_mirrored_to_legacy_fields():
    data = _sync_country_geography(
        {
            "country_code": "GN",
            "admin_level_1": "Kindia",
            "admin_level_2": "Coyah",
            "admin_level_3": "Manéah",
        }
    )
    assert data["region"] == "Kindia"
    assert data["prefecture"] == "Coyah"
    assert data["commune"] == "Manéah"


def test_other_country_does_not_invent_guinea_geography():
    data = _sync_country_geography(
        {
            "country_code": "SN",
            "admin_level_1": "Dakar",
            "admin_level_2": "Dakar",
        }
    )
    assert "region" not in data
    assert "prefecture" not in data
