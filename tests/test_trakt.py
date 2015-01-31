from __future__ import unicode_literals, division, absolute_import

from flexget.plugins.api_trakt import ApiTrakt
from tests import FlexGetBase, use_vcr


lookup_series = ApiTrakt.lookup_series


class TestTraktLookup(FlexGetBase):
    __yaml__ = """
        templates:
          global:
            trakt_lookup: yes
            # Access a tvdb field to cause lazy loading to occur
            set:
              afield: "{{tvdb_id}}{{trakt_ep_name}}"
        tasks:
          test_show_lookup:
            mock:
              - title: House
                series_name: House
          test_episode_lookup:
            mock:
              - {title: 'House.S01E02.HDTV.XViD-FlexGet'}
              - {title: 'Doctor.Who.2005.S02E03.PDTV.XViD-FlexGet'}
            series:
              - House
              - Doctor Who 2005
          test_unknown_series:
            mock:
              - {title: 'Aoeu.Htns.S01E01.htvd'}
            series:
              - Aoeu Htns
          test_date:
            mock:
              - title: the daily show 2012-6-6
            series:
              - the daily show (with jon stewart)
          test_absolute:
            mock:
              - title: naruto 128
            series:
              - naruto

    """

    @use_vcr
    def test_show_lookup(self):
        """trakt: Test Lookup (ONLINE)"""
        self.execute_task('test_show_lookup')
        entry = self.task.find_entry(title='House')
        assert entry['trakt_series_id'] == 1399, \
            'Trakt_ID should be 1339 is %s for %s' % (entry['trakt_series_id'], entry['series_name'])
        assert entry['trakt_series_status'] == 'ended', 'Series status should "ended". Got %s' \
                                                        % (entry['trakt_series_status'])

    @use_vcr
    def test_episode_lookup(self):
        """trakt: Test Lookup (ONLINE)"""
        self.execute_task('test_episode_lookup')
        entry = self.task.find_entry(title='House.S01E02.HDTV.XViD-FlexGet')
        assert entry['trakt_ep_name'] == 'Paternity', \
            '%s trakt_ep_name should be Paternity' % entry['title']
        assert entry['trakt_series_status'] == 'ended', \
            'runtime for %s is %s, should be "ended"' % (entry['title'], entry['trakt_series_status'])
        assert entry['afield'] == '73255Paternity', 'afield was not set correctly'
        assert self.task.find_entry(trakt_ep_name='School Reunion'), \
            'Failed imdb lookup Doctor Who 2005 S02E03'

    @use_vcr
    def test_unknown_series(self):
        # Test an unknown series does not cause any exceptions
        self.execute_task('test_unknown_series')
        # Make sure it didn't make a false match
        entry = self.task.find_entry('accepted', title='Aoeu.Htns.S01E01.htvd')
        assert entry.get('tvdb_id') is None, 'should not have populated tvdb data'

    @use_vcr
    def test_date(self):
        self.execute_task('test_date')
        entry = self.task.find_entry(title='the daily show 2012-6-6')
        assert entry.get('tvdb_id') is None, 'should not have populated trakt data'

    @use_vcr
    def test_absolute(self):
        self.execute_task('test_absolute')
        entry = self.task.find_entry(title='naruto 128')
        assert entry.get('tvdb_id') is None, 'should not have populated trakt data'


class TestTraktList(FlexGetBase):
    __yaml__ = """
        tasks:
          test_trakt_movies:
            trakt_list:
              username: flexgettest
              list: watchlist
              type: movies
    """

    @use_vcr
    def test_trakt_movies(self):
        self.execute_task('test_trakt_movies')
        assert len(self.task.entries) == 1
        entry = self.task.entries[0]
        assert entry['title'] == '12 Angry Men (1957)'
        assert entry['movie_name'] == '12 Angry Men'
        assert entry['movie_year'] == 1957
        assert entry['imdb_id'] == 'tt0050083'
