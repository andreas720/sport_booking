# coding=UTF-8
# Line above required to use swedish characters in file

from django.test import TestCase
from django.test import LiveServerTestCase
from django.test.client import Client
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from booking.models import ResourceType, Resource, Reservation, OverwriteLog
from booking.common import utc_now, to_timestamp
from django.conf import settings
from booking import common

from datetime import timedelta

import json


def create_user():
    user_id = User.objects.all().count() + 1
    username = 'user %s' % user_id
    password = 'pass'
    user = User.objects.create_user(username, '%s@test.com' % user_id, password)
    user.is_staff = True
    user.is_superuser = True
    user.save()
    p = user.profile
    p.postal_number = 58434
    p.phone_number = 0720226044
    p.full_name = 'boop derpatron'
    p.save()

    return user


def create_resource_type():
    resource_type_id = ResourceType.objects.all().count() + 1
    resource_type = ResourceType.objects.create()
    resource_type.translate('en')
    resource_type.type_name = 'english resource type name %s' % resource_type_id
    resource_type.general_information = 'english general info for rt %s' % resource_type_id
    resource_type.save()
    resource_type.translate('sv')
    resource_type.type_name = 'swedish resource type name %s' % resource_type_id
    resource_type.general_information = 'swedish general info for rt %s' % resource_type_id
    resource_type.save()
    return resource_type


def create_resource(resource_type):
    resource_id = Resource.objects.filter(resource_type=resource_type).count() + 1
    resource = Resource(resource_type=resource_type)
    resource.longitude = resource_id + 100 + resource_id
    resource.latitude = resource_id + 100 + resource_id
    resource.translate('en')
    resource.name = 'english resource name %s' % resource_id
    resource.specific_information = 'english resource info %s' % resource_id
    resource.save()
    resource.translate('sv')
    resource.name = 'swedish resource name %s' % resource_id
    resource.specific_information = 'swedish resource info %s' % resource_id
    resource.save()
    return resource


def create_reservation(user, resource, start, end):
    res = Reservation(user=user, resource=resource, start=start, end=end)
    res.save()
    return res


def later(hours_later):
    return utc_now() + timedelta(hours=hours_later)


def earlier(hours_earlier):
    return utc_now() - timedelta(hours=hours_earlier)


def add_test_data():
    user1 = create_user()
    user2 = create_user()
    user3 = create_user()
    user4 = create_user()
    user5 = create_user()
    user6 = create_user()
    user7 = create_user()

    rest1 = create_resource_type()
    res1 = create_resource(rest1)
    res2 = create_resource(rest1)
    res3 = create_resource(rest1)
    res4 = create_resource(rest1)
    res5 = create_resource(rest1)

    r1 = create_reservation(user1, res1, earlier(2), earlier(1))
    r2 = create_reservation(user1, res1, later(1), later(2))
    r3 = create_reservation(user1, res1, later(3), later(4))

    r4 = create_reservation(user2, res1, earlier(5), earlier(4))
    r5 = create_reservation(user2, res1, later(6), later(7))
    r6 = create_reservation(user2, res1, later(8), later(9))

    r7 = create_reservation(user3, res2, later(1), later(2))
    r8 = create_reservation(user3, res2, later(3), later(4))
    r9 = create_reservation(user3, res2, later(5), later(6))

    r10 = create_reservation(user4, res2, later(7), later(8))

    r11 = create_reservation(user7, res5, later(2), later(3))

    test_data = {
        'users': [user1, user2, user3, user4, user5, user6, user7],
        'resource_types': [rest1],
        'resources': [res1, res2, res3, res4, res5],
        'reservations': [r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11]}

    return test_data


def object_count(object_type):
    return object_type.objects.all().count()


def preserve_count(object_type):
    def real_decorator(function):
        def wrapper(self, *args, **kwargs):
            objects = object_count(object_type)
            function(self, *args, **kwargs)
            self.assertEqual(objects, object_count(object_type))
        return wrapper
    return real_decorator


def diff_count(object_type, diff):
    def real_decorator(function):
        def wrapper(self, *args, **kwargs):
            objects = object_count(object_type)
            function(self, *args, **kwargs)
            self.assertEqual(diff, object_count(object_type) - objects)
        return wrapper
    return real_decorator


class GeneralTests(TestCase):
    def test_profile_completed(self):
        username = 'user'
        password = 'pass'
        user = User.objects.create_user(username, 'user@test.com', password)
        user.is_staff = True
        user.is_superuser = True
        user.save()

        profile = user.profile
        self.assertFalse(profile.completed())
        profile.phone_number = 0720226044
        profile.save()
        self.assertFalse(profile.completed())
        profile.postal_number = 5
        profile.save()
        self.assertFalse(profile.completed())
        profile.postal_number = 58436
        profile.save()
        self.assertFalse(profile.completed())
        profile.full_name = 'barang bambadang'
        profile.save()
        self.assertTrue(profile.completed())


class ReservationTests(TestCase):
    def setUp(self):
        self.test_data = add_test_data()
        self.client = Client()
        self.user = self.test_data['users'][4]
        logged_in = self.client.login(username=self.user.username, password='pass')
        self.assertTrue(logged_in)

        self.client2 = Client()
        self.user2 = self.test_data['users'][6]
        logged_in = self.client2.login(username=self.user2.username, password='pass')
        self.assertTrue(logged_in)

    def test_ensure_solidness(self):
        r = self.test_data['reservations']
        self.assertTrue(r[0].is_solid())
        self.assertTrue(r[1].is_solid())
        self.assertFalse(r[2].is_solid())

        self.assertTrue(r[3].is_solid())
        self.assertTrue(r[4].is_solid())
        self.assertFalse(r[5].is_solid())

        self.assertTrue(r[6].is_solid())
        self.assertFalse(r[7].is_solid())
        self.assertFalse(r[8].is_solid())

        self.assertTrue(r[9].is_solid())

        self.assertTrue(r[10].is_solid())

    @preserve_count(Reservation)
    def test_delete_reservation_success(self):
        r_id = self.test_data['reservations'][10].id
        response = self.client2.post('/delete_reservation/', {
            'id': r_id})
        self.assertEqual(response.status_code, 200)
        res_content = json.loads(response.content)

        self.assertEqual(1, res_content['deleted'])
        res = Reservation.objects.get(id=r_id)
        self.assertTrue(res.deleted)

    @preserve_count(Reservation)
    def test_fail_delete_others_reservation(self):
        r_id = self.test_data['reservations'][9].id
        response = self.client.post('/delete_reservation/', {
            'id': r_id})
        self.assertEqual(response.status_code, 403)
        res = Reservation.objects.get(id=r_id)
        self.assertFalse(res.deleted)

    @diff_count(Reservation, 1)
    def test_reserve_over_deleted_success(self):
        res = self.test_data['reservations'][10]
        response = self.client2.post('/delete_reservation/', {
            'id': res.id})
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/make_reservation/', {
            'start': to_timestamp(res.start),
            'end': to_timestamp(res.end),
            'resource_id': res.resource_id})
        self.assertEqual(response.status_code, 200)
        res_content = json.loads(response.content)
        self.assertTrue(Reservation.objects.filter(id=res_content['id']).exists())

    def test_deleted_solidity(self):
        res = self.test_data['reservations'][10]
        self.assertTrue(res.is_solid())

        response = self.client2.post('/make_reservation/', {
            'start': to_timestamp(later(4)),
            'end': to_timestamp(later(5)),
            'resource_id': res.resource_id})
        self.assertEqual(response.status_code, 200)
        res_content = json.loads(response.content)
        self.assertFalse(Reservation.objects.get(id=res_content['id']).is_solid())
        self.assertTrue(res.is_solid())

        response = self.client2.post('/delete_reservation/', {
            'id': res.id})

        self.assertTrue(Reservation.objects.get(id=res_content['id']).is_solid())
        self.assertFalse(Reservation.objects.get(id=res.id).is_solid())

    @diff_count(Reservation, 1)
    def test_simple_reservation_success(self):
        resource = self.test_data['resources'][2]

        response = self.client.post('/make_reservation/', {
            'start': to_timestamp(later(2)),
            'end': to_timestamp(later(2 + settings.MAX_RESERVATION_LENGTH)),
            'resource_id': resource.id})
        self.assertEqual(response.status_code, 200)
        res_content = json.loads(response.content)
        self.assertTrue(Reservation.objects.filter(id=res_content['id']).exists())

    @preserve_count(Reservation)
    def test_banned_reservation_failure(self):
        resource = self.test_data['resources'][2]
        profile = self.user.profile
        profile.is_banned = 'banned because of tests'
        profile.save()

        response = self.client.post('/make_reservation/', {
            'start': to_timestamp(later(2)),
            'end': to_timestamp(later(2 + settings.MAX_RESERVATION_LENGTH)),
            'resource_id': resource.id})
        self.assertEqual(response.status_code, 403)

    @preserve_count(Reservation)
    def test_incomplete_profile_reservation_failure(self):
        resource = self.test_data['resources'][2]
        profile = self.user.profile
        profile.full_name = ''
        profile.save()

        response = self.client.post('/make_reservation/', {
            'start': to_timestamp(later(2)),
            'end': to_timestamp(later(2 + settings.MAX_RESERVATION_LENGTH)),
            'resource_id': resource.id})
        self.assertEqual(response.status_code, 403)

    @preserve_count(Reservation)
    def test_fail_new_reservation_in_past(self):
        resource = self.test_data['resources'][2]

        response = self.client.post('/make_reservation/', {
            'start': to_timestamp(earlier(2)),
            'end': to_timestamp(earlier(1)),
            'resource_id': resource.id})
        self.assertEqual(response.status_code, 403)

    @preserve_count(Reservation)
    def test_fail_new_reservation_starts_after_ends(self):
        resource = self.test_data['resources'][2]

        response = self.client.post('/make_reservation/', {
            'start': to_timestamp(later(2)),
            'end': to_timestamp(later(1)),
            'resource_id': resource.id})
        self.assertEqual(response.status_code, 403)

    @diff_count(Reservation, 2)
    def test_fail_third_reservation(self):
        resource = self.test_data['resources'][2]

        response = self.client.post('/make_reservation/', {
            'start': to_timestamp(later(1)),
            'end': to_timestamp(later(2)),
            'resource_id': resource.id})
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/make_reservation/', {
            'start': to_timestamp(later(3)),
            'end': to_timestamp(later(4)),
            'resource_id': resource.id})
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/make_reservation/', {
            'start': to_timestamp(later(5)),
            'end': to_timestamp(later(6)),
            'resource_id': resource.id})
        self.assertEqual(response.status_code, 403)

    @preserve_count(Reservation)
    def test_fail_too_long_reservation(self):
        resource1 = self.test_data['resources'][2]
        start = 0
        end = 1 + settings.MAX_RESERVATION_LENGTH

        response = self.client.post('/make_reservation/', {
            'start': to_timestamp(later(start)),
            'end': to_timestamp(later(end)),
            'resource_id': resource1.id})
        self.assertEqual(response.status_code, 403)

    @diff_count(Reservation, 2)
    def test_succeed_two_serial_reservations(self):
        resource1 = self.test_data['resources'][2]

        response = self.client.post('/make_reservation/', {
            'start': to_timestamp(later(1)),
            'end': to_timestamp(later(2)),
            'resource_id': resource1.id})
        self.assertEqual(response.status_code, 200)
        res_content = json.loads(response.content)
        self.assertTrue(Reservation.objects.filter(id=res_content['id']).exists())

        response = self.client.post('/make_reservation/', {
            'start': to_timestamp(later(2)),
            'end': to_timestamp(later(3)),
            'resource_id': resource1.id})
        self.assertEqual(response.status_code, 200)
        res_content = json.loads(response.content)
        self.assertTrue(Reservation.objects.filter(id=res_content['id']).exists())

    @diff_count(Reservation, 1)
    def test_fail_overlapping_reservations(self):
        resource1 = self.test_data['resources'][2]
        resource2 = self.test_data['resources'][3]

        forbidden_reservations = [
            (later(3.2), later(3.8)),
            (later(3.1), later(3.9)),
            (later(3.3), later(3.7)),
            (later(3.2), later(3.3)),
            (later(3.5), later(3.8)),
            (later(3.5), later(4)),
            (later(3), later(3.5))]

        response = self.client.post('/make_reservation/', {
            'start': to_timestamp(later(3.2)),
            'end': to_timestamp(later(3.8)),
            'resource_id': resource1.id})
        self.assertEqual(response.status_code, 200)

        for (start, end) in forbidden_reservations:
            response = self.client.post('/make_reservation/', {
                'start': to_timestamp(start),
                'end': to_timestamp(end),
                'resource_id': resource2.id})
            self.assertEqual(response.status_code, 403)

    def test_fail_reserve_busy_resource(self):
        c = Client()
        other_user = self.test_data['users'][5]
        c.login(username=other_user.username, password='pass')

        resource1 = self.test_data['resources'][2]

        response = c.post('/make_reservation/', {
            'start': to_timestamp(later(1)),
            'end': to_timestamp(later(2)),
            'resource_id': resource1.id})
        self.assertEqual(response.status_code, 200)

        colliding_reservations = [
            (later(0.5), later(1.1)),
            (later(1), later(2)),
            (later(1.1), later(2.1)),
            (later(1.9), later(2.1))]

        for (start, end) in colliding_reservations:
            response = self.client.post('/make_reservation/', {
                'start': to_timestamp(start),
                'end': to_timestamp(end),
                'resource_id': resource1.id})
            self.assertEqual(response.status_code, 403)

    @preserve_count(OverwriteLog)
    @diff_count(Reservation, 3)
    def test_fail_overwrite_with_preliminary(self):
        c = Client()
        other_user = self.test_data['users'][5]
        c.login(username=other_user.username, password='pass')

        resource1 = self.test_data['resources'][2]

        response = c.post('/make_reservation/', {
            'start': to_timestamp(later(3)),
            'end': to_timestamp(later(4)),
            'resource_id': resource1.id})
        self.assertEqual(response.status_code, 200)
        res_content = json.loads(response.content)
        id_res1 = res_content['id']

        response = c.post('/make_reservation/', {
            'start': to_timestamp(later(5)),
            'end': to_timestamp(later(6)),
            'resource_id': resource1.id})
        self.assertEqual(response.status_code, 200)
        res_content = json.loads(response.content)
        id_res2 = res_content['id']

        response = self.client.post('/make_reservation/', {
            'start': to_timestamp(later(1)),
            'end': to_timestamp(later(2)),
            'resource_id': resource1.id})
        self.assertEqual(response.status_code, 200)
        res_content = json.loads(response.content)
        id_res3 = res_content['id']

        response = self.client.post('/make_reservation/', {
            'start': to_timestamp(later(1)),
            'end': to_timestamp(later(2)),
            'resource_id': resource1.id})
        self.assertEqual(response.status_code, 403)

        res1 = get_object_or_404(Reservation, pk=int(id_res1))
        res2 = get_object_or_404(Reservation, pk=int(id_res2))
        res3 = get_object_or_404(Reservation, pk=int(id_res3))

        self.assertFalse(res1.deleted)
        self.assertFalse(res2.deleted)
        self.assertFalse(res3.deleted)

    @diff_count(Reservation, 3)
    @diff_count(OverwriteLog, 1)
    def test_overwrite_preliminary(self):
        c = Client()
        other_user = self.test_data['users'][5]
        c.login(username=other_user.username, password='pass')

        resource1 = self.test_data['resources'][2]

        response = c.post('/make_reservation/', {
            'start': to_timestamp(later(1)),
            'end': to_timestamp(later(2)),
            'resource_id': resource1.id})
        self.assertEqual(response.status_code, 200)
        res_content = json.loads(response.content)
        id_res1 = res_content['id']

        response = c.post('/make_reservation/', {
            'start': to_timestamp(later(3)),
            'end': to_timestamp(later(4)),
            'resource_id': resource1.id})
        self.assertEqual(response.status_code, 200)
        res_content = json.loads(response.content)
        id_res2 = res_content['id']

        response = self.client.post('/make_reservation/', {
            'start': to_timestamp(later(3)),
            'end': to_timestamp(later(4)),
            'resource_id': resource1.id})
        self.assertEqual(response.status_code, 200)
        res_content = json.loads(response.content)
        id_res3 = res_content['id']

        res1 = get_object_or_404(Reservation, pk=int(id_res1))
        res2 = get_object_or_404(Reservation, pk=int(id_res2))
        res3 = get_object_or_404(Reservation, pk=int(id_res3))

        self.assertFalse(res1.deleted)
        self.assertTrue(res2.deleted)
        self.assertFalse(res3.deleted)

        self.assertTrue(OverwriteLog.objects.filter(
            deleted_reservation=res2,
            replacing_reservation=res3).exists())

    @preserve_count(Reservation)
    def test_fail_unauthorized_reservation(self):
        c = Client()
        resource = self.test_data['resources'][2]

        response = c.post('/make_reservation/', {
            'start': to_timestamp(later(2)),
            'end': to_timestamp(later(3)),
            'resource_id': resource.id})
        self.assertEqual(response.status_code, 302)
        # Normally one would expect HTTP 401 for unauthorized requests,
        # but django instead sends a redirect to the login page.


class TimeTests(TestCase):
    def setUp(self):
        pass

    def assert_approx_equal(self, dt1, dt2):
        """
        Checks that two datetime objects are equal without respects to
        timezone or milliseconds, things that get lost in timestamp conversion.
        """
        self.assertEqual(dt1.date(), dt2.date())
        self.assertEqual(dt1.time().hour, dt2.time().hour)
        self.assertEqual(dt1.time().minute, dt2.time().minute)
        self.assertEqual(dt1.time().second, dt2.time().second)

    def test_utc_conversions(self):
        now = common.utc_now()
        now_ts = common.to_timestamp(now)
        now_from_ts = common.from_timestamp(now_ts)
        self.assert_approx_equal(now, now_from_ts)

    def test_utc_sv_conversions(self):
        now = common.utc_now()
        local_now = common.as_local_time(now)

        self.assertEqual(now, local_now)
        self.assertNotEquals(now.tzname(), local_now.tzname())

        ts_sv = common.to_timestamp(local_now)
        ts_utc = common.to_timestamp(now)

        self.assertEqual(ts_sv, ts_utc)

        self.assert_approx_equal(common.from_timestamp(ts_sv), common.from_timestamp(ts_utc))

    def test_sv_ts_sv(self):
        utc_now = common.utc_now()
        local_now = common.as_local_time(utc_now)

        ts = common.to_timestamp(local_now)

        utc_from_ts = common.from_timestamp(ts)
        local_from_ts = common.as_local_time(utc_from_ts)

        self.assert_approx_equal(utc_now, utc_from_ts)
        self.assert_approx_equal(local_now, local_from_ts)
        self.assertEqual(utc_now, local_now)
        self.assertEqual(utc_from_ts, local_from_ts)


class ManualTests(LiveServerTestCase):
    def setUp(self):
        self.test_data = add_test_data()

    def test_run_test_server_with_test_data(self):
        try:
            raw_input('\nAccepting tests on http://127.0.0.1:8081 until Enter is pressed...\n')
        except EOFError:
            pass
