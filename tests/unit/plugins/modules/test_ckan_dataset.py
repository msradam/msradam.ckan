# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Adam Munawar Rahman <msrahmanadam@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.msradam.ckan.plugins.modules import ckan_dataset as mod


def test_normalize():
    assert mod.normalize(True) is True
    assert mod.normalize(False) is False
    assert mod.normalize(None) is None
    assert mod.normalize(5) == u'5'
    assert mod.normalize('text') == u'text'


def test_desired_scalars_maps_source_url_and_skips_unset():
    params = {'title': 'Title', 'source_url': 'http://example/data.csv', 'private': True, 'notes': None}
    assert mod.desired_scalars(params) == {
        'title': 'Title',
        'url': 'http://example/data.csv',
        'private': True,
    }


def test_desired_tags_sorted_unique():
    assert mod.desired_tags({'tags': ['b', 'a', 'b']}) == ['a', 'b']
    assert mod.desired_tags({'tags': []}) == []
    assert mod.desired_tags({}) is None


def test_desired_groups_sorted_unique():
    assert mod.desired_groups({'groups': ['b', 'a', 'b']}) == ['a', 'b']
    assert mod.desired_groups({'groups': []}) == []
    assert mod.desired_groups({}) is None


def test_desired_extras_stringifies_values():
    assert mod.desired_extras({'extras': {'count': 5, 'region': 'national'}}) == {
        'count': '5',
        'region': 'national',
    }
    assert mod.desired_extras({}) is None


def test_owner_org_matches_by_id_or_name():
    existing = {'owner_org': 'org-uuid', 'organization': {'id': 'org-uuid', 'name': 'env-agency'}}
    assert mod.owner_org_matches(existing, 'env-agency')
    assert mod.owner_org_matches(existing, 'org-uuid')
    assert not mod.owner_org_matches(existing, 'other-org')


def _active(**extra):
    base = {'state': 'active', 'tags': [], 'groups': [], 'extras': []}
    base.update(extra)
    return base


def test_compute_changes_no_diff():
    existing = _active(title='Same', notes='Body')
    changes, before, after = mod.compute_changes(existing, {'title': 'Same', 'notes': 'Body'}, None, None, None)
    assert changes == {}
    assert before == {} and after == {}


def test_compute_changes_scalar_diff():
    existing = _active(title='Old')
    changes, before, after = mod.compute_changes(existing, {'title': 'New'}, None, None, None)
    assert changes == {'title': 'New'}
    assert before == {'title': 'Old'}
    assert after == {'title': 'New'}


def test_compute_changes_private_bool():
    existing = _active(private=False)
    changes, dummy, dummy = mod.compute_changes(existing, {'private': True}, None, None, None)
    assert changes == {'private': True}
    # No spurious change when already matching.
    changes, dummy, dummy = mod.compute_changes(_active(private=True), {'private': True}, None, None, None)
    assert changes == {}


def test_compute_changes_tags_replace():
    existing = _active(tags=[{'name': 'a'}])
    changes, before, after = mod.compute_changes(existing, {}, ['b', 'a'], None, None)
    assert changes['tags'] == [{'name': 'a'}, {'name': 'b'}]
    assert before['tags'] == ['a']
    assert after['tags'] == ['a', 'b']
    # Equal tag sets are not a change.
    changes, dummy, dummy = mod.compute_changes(_active(tags=[{'name': 'a'}]), {}, ['a'], None, None)
    assert 'tags' not in changes


def test_compute_changes_groups_replace():
    existing = _active(groups=[{'name': 'climate'}])
    changes, before, after = mod.compute_changes(existing, {}, None, ['climate', 'transport'], None)
    assert changes['groups'] == [{'name': 'climate'}, {'name': 'transport'}]
    assert before['groups'] == ['climate']
    assert after['groups'] == ['climate', 'transport']
    # Equal group sets are not a change.
    changes, dummy, dummy = mod.compute_changes(
        _active(groups=[{'name': 'climate'}]), {}, None, ['climate'], None
    )
    assert 'groups' not in changes
    # Empty list removes all groups.
    changes, dummy, dummy = mod.compute_changes(_active(groups=[{'name': 'climate'}]), {}, None, [], None)
    assert changes['groups'] == []


def test_compute_changes_extras_replace():
    existing = _active(extras=[{'key': 'k', 'value': 'old'}])
    changes, dummy, dummy = mod.compute_changes(existing, {}, None, None, {'k': 'new'})
    assert changes['extras'] == [{'key': 'k', 'value': 'new'}]
    # Equal extras are not a change.
    changes, dummy, dummy = mod.compute_changes(
        _active(extras=[{'key': 'k', 'value': 'v'}]), {}, None, None, {'k': 'v'}
    )
    assert 'extras' not in changes


def test_compute_changes_reactivates_deleted():
    existing = {'state': 'deleted', 'tags': [], 'groups': [], 'extras': []}
    changes, before, after = mod.compute_changes(existing, {}, None, None, None)
    assert changes.get('state') == 'active'
    assert before['state'] == 'deleted'
    assert after['state'] == 'active'


def test_compute_changes_owner_org_no_change_when_name_matches_id():
    existing = _active(owner_org='org-uuid', organization={'id': 'org-uuid', 'name': 'env-agency'})
    changes, dummy, dummy = mod.compute_changes(existing, {'owner_org': 'env-agency'}, None, None, None)
    assert 'owner_org' not in changes
