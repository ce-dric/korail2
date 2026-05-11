# -*- coding: utf-8 -*-
"""
    korail2.korail2
    ~~~~~~~~~~~~~~~

    :copyright: (c) 2014 by Taehoon Kim.
    :license: BSD, see LICENSE for more details.
"""
import re
import requests
import itertools
import sys
import base64
import time
import random
import string

from datetime import datetime, timedelta
from six import with_metaclass
from pprint import pprint
from datetime import timezone
from Crypto.Util.Padding import pad
from Crypto.Cipher import AES

try:
    # noinspection PyPackageRequirements
    import simplejson as json
except ImportError:
    import json


def _python3():
    return sys.version_info > (3, 0)

if _python3():
    from functools import reduce

EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")
PHONE_NUMBER_REGEX = re.compile(r"(\d{3})-(\d{3,4})-(\d{4})")

SCHEME = "https"
KORAIL_HOST = "smart.letskorail.com"
KORAIL_PORT = "443"

KORAIL_DOMAIN = "%s://%s:%s" % (SCHEME, KORAIL_HOST, KORAIL_PORT)
KORAIL_MOBILE = "%s/classes/com.korail.mobile" % KORAIL_DOMAIN

KORAIL_LOGIN = "%s.login.Login" % KORAIL_MOBILE
KORAIL_LOGOUT = "%s.common.logout" % KORAIL_MOBILE
KORAIL_SEARCH_SCHEDULE = "%s.seatMovie.ScheduleView" % KORAIL_MOBILE
KORAIL_TICKETRESERVATION = "%s.certification.TicketReservation" % KORAIL_MOBILE
KORAIL_REFUND = "%s.refunds.RefundsRequest" % KORAIL_MOBILE
KORAIL_MYTICKETLIST = "%s.myTicket.MyTicketList" % KORAIL_MOBILE
KORAIL_MYTICKET_SEAT = "%s.refunds.SelTicketInfo" % KORAIL_MOBILE

KORAIL_MYRESERVATIONLIST = "%s.reservation.ReservationView" % KORAIL_MOBILE
KORAIL_CANCEL = "%s.reservationCancel.ReservationCancelChk" % KORAIL_MOBILE

KORAIL_STATION_DB = "%s.common.stationinfo?device=ip" % KORAIL_MOBILE
KORAIL_STATION_DB_DATA = "%s.common.stationdata" % KORAIL_MOBILE
KORAIL_EVENT = "%s.common.event" % KORAIL_MOBILE
KORAIL_PAYMENT = "%s/ebizmw/PrdPkgMainList.do" % KORAIL_DOMAIN
KORAIL_PAYMENT_VOUCHER = "%s/ebizmw/PrdPkgBoucherView.do" % KORAIL_DOMAIN

KORAIL_CODE = "%s.common.code.do" % KORAIL_MOBILE
KORAIL_NCARD_SCHEDULE_VIEW = "%s.research.dcntCrdScheduleView.do" % KORAIL_MOBILE
KORAIL_NCARD_USE_HISTORY = "%s.ticket.dcntCrdUseQry.do" % KORAIL_MOBILE

NCARD_DISCOUNT_CODE = "153"

DEFAULT_USER_AGENT = "Dalvik/2.1.0 (Linux; U; Android 13; SM-S928N Build/UP1A.231005.007)"

DYNAPATH_PATHS = [
    "/classes/com.korail.mobile.certification.TicketReservation",
    "/classes/com.korail.mobile.nonMember.NonMemTicket",
    "/classes/com.korail.mobile.seatMovie.ScheduleView",
    "/classes/com.korail.mobile.seatMovie.ScheduleViewSpecial",
    "/classes/com.korail.mobile.trn.prcFare.do",
    "/classes/com.korail.mobile.login.Login"
]

class DynaPathMasterEngine:
    APP_ID = "com.korail.talk"
    AS_VALUE = "%5B38ff229cb34c7dda8e28220a2d750cce%5D"
    DEVICE_MODEL = "SM-S928N"
    OS_TYPE = "Android"
    SDK_VERSION = "v1"

    def __init__(self):
        self.TABLE = "3FE9jgRD4KdCyuawklqGJYmvfMn15P7US8XbxeLQtWT6OicBAopINs2Vh0HZrz"
        self.I8, self.I9, self.I10 = 161, 30, 2
        self.app_start_ts = str(int(time.time() * 1000))

    def string2xA1s(self, data_str):
        result = []
        i = 0
        while i < len(data_str):
            cp = ord(data_str[i])
            i += 1
            if cp < 128: result.append(cp)
            elif cp < 2048:
                result.append(128 | ((cp >> 7) & 15))
                result.append(cp & 127)
            elif cp >= 262144:
                result.append(160)
                result.append((cp >> 14) & 127)
                result.append((cp >> 7) & 127)
                result.append(cp & 127)
            elif (63488 & cp) != 55296:
                result.append(((cp >> 14) & 15) | 144)
                result.append((cp >> 7) & 127)
                result.append(cp & 127)
        return result

    def make_key(self, key_str):
        big_int_add = 0
        for char in key_str:
            cp = ord(char)
            i9_bit = 32768
            for _ in range(16):
                if (i9_bit & cp) != 0: break
                i9_bit >>= 1
            big_int_add = (big_int_add * (i9_bit << 1)) + cp
        return big_int_add

    def _internal_i(self, base_table, remainder, encode_size, current_sb):
        j8_count = 0
        for k in range(len(base_table)):
            char = base_table[k]
            if char not in current_sb:
                if j8_count == remainder: return char
                j8_count += 1
        return ' '

    def make_encode_table(self, num, encode_size, base_table):
        sb = ""
        temp_num = num
        for i in range(encode_size):
            j8_divisor = encode_size - i
            remainder = temp_num % j8_divisor
            char = self._internal_i(base_table, remainder, len(base_table), sb)
            sb += char
            temp_num //= j8_divisor
        return sb

    def encode_normal_be(self, data_str, table, i8=161, i9=30, i10=2):
        list_data = self.string2xA1s(data_str)
        sb, i_arr = [], [0] * (i10 + 1)
        idx, size = 0, len(list_data) % i10
        size2 = len(list_data) - size
        while idx < size2:
            val = 0
            for _ in range(i10):
                val = (val * i8) + list_data[idx]
                idx += 1
            for i in range(i10 + 1):
                i_arr[i] = val % i9
                val //= i9
            for i in range(i10, -1, -1): sb.append(table[i_arr[i]])
        if size > 0:
            val = 0
            for _ in range(size):
                val = (val * i8) + list_data[idx]
                idx += 1
            for i in range(size + 1):
                i_arr[i] = val % i9
                val //= i9
            while size >= 0:
                sb.append(table[i_arr[size]])
                size -= 1
        return "".join(sb)

    def generate_token(self, device_id, ts, rand):
        plaintext = (f"ai={self.APP_ID}&di={device_id}&as={self.AS_VALUE}&"
                     f"su=false&dbg=false&emu=false&hk=false&it={self.app_start_ts}&"
                     f"ts={ts}&rt=0&os=13&dm={self.DEVICE_MODEL}&st={self.OS_TYPE}&sv={self.SDK_VERSION}")

        dyn_key = f"v1+{rand}+{ts}"
        key_enc = self.encode_normal_be(dyn_key, self.TABLE, self.I8, self.I9, self.I10)
        big_key = self.make_key(dyn_key)
        custom_table = self.make_encode_table(big_key, self.I9, self.TABLE)
        body_enc = self.encode_normal_be(plaintext, custom_table, self.I8, self.I9, self.I10)
        return f"bEeEP{self.TABLE[len(key_enc)]}{key_enc}{body_enc}"

def _get_utf8(data, key, default=None):
    v = data.get(key, default)

    if _python3():
        return v

    if isinstance(v, basestring):
        return v.encode('utf-8')
    else:
        return v


def _get_first(data, keys, default=None):
    for key in keys:
        value = _get_utf8(data, key)
        if value is not None:
            return value
    return default


class Schedule(object):
    """Korail train object. Highly inspired by `korail.py
    <https://raw.githubusercontent.com/devxoul/korail/master/korail/korail.py>`_
    by `Suyeol Jeon <http://xoul.kr/>`_ at 2014.
    """

    # : 기차 종류
    # : 00: KTX
    #: 01: 새마을호
    #: 02: 무궁화호
    #: 03: 통근열차
    #: 04: 누리로
    #: 05: 전체 (검색시에만 사용)
    #: 06: 공학직통
    #: 07: KTX-산천
    #: 08: ITX-새마을
    #: 09: ITX-청춘
    train_type = None  # h_trn_clsf_cd, selGoTrain

    train_group = None # h_trn_gp_cd

    #: 기차 종류 이름
    train_type_name = None  # h_trn_clsf_nm

    #: 기차 번호
    train_no = None  # h_trn_no

    #: 출발역 이름
    dep_name = None  # h_dpt_rs_stn_nm

    #: 출발역 코드
    dep_code = None  # h_dpt_rs_stn_cd

    #: 출발 날짜 (yyyyMMdd)
    dep_date = None  # h_dpt_dt

    #: 출발 시각 (hhmmss)
    dep_time = None  # h_dpt_tm

    #: 도착역 이름
    arr_name = None  # h_arv_rs_stn_nm

    #: 도착역 코드
    arr_code = None  # h_arv_rs_stn_cd

    #: 도착 날짜 (yyyyMMdd)
    arr_date = None  # h_arv_dt

    #: 도착 시각 (hhmmss)
    arr_time = None  # h_arv_tm

    #: 운행 날짜 (yyyyMMdd)
    run_date = None  # h_run_dt


    def __init__(self, data):

        self.train_type = _get_utf8(data, 'h_trn_clsf_cd')
        self.train_type_name = _get_utf8(data, 'h_trn_clsf_nm')
        self.train_group = _get_utf8(data, 'h_trn_gp_cd')
        self.train_no = _get_utf8(data, 'h_trn_no')
        self.delay_time = _get_utf8(data, 'h_expct_dlay_hr')

        self.dep_name = _get_utf8(data, 'h_dpt_rs_stn_nm')
        self.dep_code = _get_utf8(data, 'h_dpt_rs_stn_cd')
        self.dep_date = _get_utf8(data, 'h_dpt_dt')
        self.dep_time = _get_utf8(data, 'h_dpt_tm')

        self.arr_name = _get_utf8(data, 'h_arv_rs_stn_nm')
        self.arr_code = _get_utf8(data, 'h_arv_rs_stn_cd')
        self.arr_date = _get_utf8(data, 'h_arv_dt')
        self.arr_time = _get_utf8(data, 'h_arv_tm')

        self.run_date = _get_utf8(data, 'h_run_dt')

    def __repr__(self):
        dep_time = "%s:%s" % (self.dep_time[:2], self.dep_time[2:4])
        arr_time = "%s:%s" % (self.arr_time[:2], self.arr_time[2:4])

        dep_date = "%s월 %s일" % (int(self.dep_date[4:6]), int(self.dep_date[6:]))

        repr_str = '[%s] %s, %s~%s(%s~%s)' % (
            self.train_type_name,
            dep_date,
            self.dep_name,
            self.arr_name,
            dep_time,
            arr_time,
        )

        return repr_str


class Train(Schedule):
    # : 지연 시간 (hhmm)
    delay_time = None  # h_expct_dlay_hr

    # : 예약 가능 여부
    reserve_possible = False  # h_rsv_psb_flg ('Y' or 'N')

    #: 예약 가능 여부
    reserve_possible_name = None  # h_rsv_psb_nm

    #: 특실 예약가능 여부
    #: 00: 특실 없음
    #: 11: 예약 가능
    #: 13: 매진
    special_seat = None  # h_spe_rsv_cd

    #: 일반실 예약가능 여부
    #: 00: 일반실 없음
    #: 11: 예약 가능
    #: 13: 매진
    general_seat = None  # h_gen_rsv_cd

    #: 예약 대기 가능 여부
    #: -2: 좌석 있음
    #: 9: 예약 대기 (일반석)
    #: 0: 예약 대기 없음 (매진)
    ## 특실의 경우 케이스 예약대기도 09를 사용하는지 확인이 필요함
    wait_reserve_flag = None # h_wait_rsv_flg

    def __init__(self, data):
        super(Train, self).__init__(data)
        self.reserve_possible = _get_utf8(data, 'h_rsv_psb_flg')
        self.reserve_possible_name = _get_utf8(data, 'h_rsv_psb_nm')

        self.special_seat = _get_utf8(data, 'h_spe_rsv_cd')
        self.general_seat = _get_utf8(data, 'h_gen_rsv_cd')

        self.wait_reserve_flag = _get_utf8(data, 'h_wait_rsv_flg')
        if self.wait_reserve_flag:
            self.wait_reserve_flag = int(self.wait_reserve_flag)


    def __repr__(self):
        repr_str = super(Train, self).__repr__()

        if self.reserve_possible_name is not None:
            seats = []
            if self.has_special_seat():
                seats.append("특실")

            if self.has_general_seat():
                seats.append("일반실")

            if self.has_general_waiting_list():
                seats.append("예약 대기(일반)")

            repr_str += " " + (",".join(seats)) + " " + self.reserve_possible_name.replace('\n', ' ')

        return repr_str

    def has_special_seat(self):
        return self.special_seat == '11'

    def has_general_seat(self):
        return self.general_seat == '11'

    def has_seat(self):
        return self.has_general_seat() or self.has_special_seat()

    def has_waiting_list(self):
        return self.has_general_waiting_list()

    def has_general_waiting_list(self):
        return self.wait_reserve_flag == 9


class NCardTrain(Train):
    """N-card discounted ticket train candidate returned by KorailTalk."""

    def __init__(self, data):
        self.train_type = _get_first(data, ('h_trn_clsf_cd', 'trnClsfCd', 'trnGpCd'))
        self.train_type_name = _get_first(data, ('h_trn_clsf_nm', 'trnClsfNm', 'dturNm'))
        self.train_group = _get_first(data, ('h_trn_gp_cd', 'trnGpCd'))
        self.train_no = _get_first(data, ('h_trn_no', 'trnNo'))
        self.delay_time = _get_first(data, ('h_expct_dlay_hr', 'expctDlayHr'), '')

        self.dep_name = _get_first(data, ('h_dpt_rs_stn_nm', 'dptRsStnNm'))
        self.dep_code = _get_first(data, ('h_dpt_rs_stn_cd', 'dptRsStnCd'))
        self.dep_date = _get_first(data, ('h_dpt_dt', 'dptDt', 'runDt'))
        self.dep_time = _get_first(data, ('h_dpt_tm', 'dptTm'))

        self.arr_name = _get_first(data, ('h_arv_rs_stn_nm', 'arvRsStnNm'))
        self.arr_code = _get_first(data, ('h_arv_rs_stn_cd', 'arvRsStnCd'))
        self.arr_date = _get_first(data, ('h_arv_dt', 'arvDt', 'runDt'))
        self.arr_time = _get_first(data, ('h_arv_tm', 'arvTm'))

        self.run_date = _get_first(data, ('h_run_dt', 'runDt', 'dptDt'))
        self.reserve_possible = _get_first(data, ('h_rsv_psb_flg', 'rsvPsbFlg'), 'Y')
        self.reserve_possible_name = _get_first(data, ('h_rsv_psb_nm', 'rsvPsbNm'), '')
        self.special_seat = _get_first(data, ('h_spe_rsv_cd', 'speRsvCd'), '00')
        self.general_seat = _get_first(data, ('h_gen_rsv_cd', 'genRsvCd'), '11')
        self.wait_reserve_flag = _get_first(data, ('h_wait_rsv_flg', 'waitRsvFlg'))
        if self.wait_reserve_flag:
            self.wait_reserve_flag = int(self.wait_reserve_flag)

        self.price = _get_first(data, ('cmtrPrc', 'h_rcvd_amt'))
        self.route_code = _get_first(data, ('routCd', 'h_rout_cd'))
        self.route_name = _get_first(data, ('dturNm', 'h_rout_nm'))
        self.raw = data

    def __repr__(self):
        train_name = self.train_type_name or self.train_group or "NCard"
        route = "%s~%s" % (self.dep_name or "", self.arr_name or "")
        if self.dep_time and self.arr_time:
            route += "(%s:%s~%s:%s)" % (
                self.dep_time[:2], self.dep_time[2:4],
                self.arr_time[:2], self.arr_time[2:4],
            )
        if self.price:
            route += " %s원" % self.price
        return "[%s] %s" % (train_name, route)


class NCard:
    """Owned N-card metadata from KorailTalk's MyTicket flow."""

    def __init__(self, ticket_data, detail_data=None):
        detail_data = detail_data or {}
        dcnt_info = detail_data.get('dcnt_crd_info') or {}
        segments = dcnt_info.get('appSegList') or dcnt_info.get('appSeg_info') or []

        self.raw_ticket = ticket_data
        self.raw_detail = detail_data
        self.ticket_kind_code = _get_utf8(ticket_data, 'h_tk_knd_cd')
        self.ticket_kind_name = _get_utf8(detail_data, 'h_tk_knd_nm') or _get_utf8(ticket_data, 'h_tk_knd_nm')
        self.valid = _get_utf8(ticket_data, 'cmtrVlidFlg')
        self.dep_name = _get_utf8(ticket_data, 'h_dpt_rs_stn_nm')
        self.arr_name = _get_utf8(ticket_data, 'h_arv_rs_stn_nm')
        self.sale_date = _get_utf8(ticket_data, 'h_orgtk_sale_dt')
        self.sale_info1 = _get_utf8(ticket_data, 'h_orgtk_wct_no')
        self.sale_info2 = _get_utf8(ticket_data, 'h_orgtk_ret_sale_dt')
        self.sale_info3 = _get_utf8(ticket_data, 'h_orgtk_sale_sqno')
        self.sale_info4 = _get_utf8(ticket_data, 'h_orgtk_ret_pwd')
        self.price = _get_utf8(ticket_data, 'h_rcvd_amt')
        self.pnr_no = _get_utf8(ticket_data, 'h_pnr_no')
        self.discount_card_no = _get_utf8(dcnt_info, 'h_dcnt_crd_no')
        self.term_extension_possible = _get_utf8(dcnt_info, 'h_dcnt_crd_trm_extn_psb_flg')
        self.reservation_discount_card_no = _get_utf8(detail_data, 'h_rsv_disc_crd_no')
        self.reservation_discount_card_name = _get_utf8(detail_data, 'h_rsv_disc_crd_knd_nm')
        self.segments = segments

    def get_ticket_no(self):
        return "-".join(map(str, (self.sale_info1, self.sale_info2, self.sale_info3, self.sale_info4)))

    @property
    def dcnt_card_no(self):
        return self.discount_card_no

    def __repr__(self):
        route = "%s~%s" % (self.dep_name or "", self.arr_name or "")
        kind = self.ticket_kind_name or "NCard"
        return "[%s] %s %s" % (kind, route, self.get_ticket_no())


class Ticket(Train):
    """Ticket object"""

    # : 열차 번호
    car_no = None  # h_srcar_no

    # : 자리 갯수
    seat_no_count = None  # h_seat_cnt  ex) 001

    #: 자리 번호
    seat_no = None  # h_seat_no

    #: 자리 번호
    seat_no_end = None  # h_seat_no_end

    #: 구매자 성함
    buyer_name = None  # h_buy_ps_nm

    #: 구매 날짜 (yyyyMMdd)
    sale_date = None  # h_orgtk_sale_dt

    #: 구매 정보1
    sale_info1 = None  # h_orgtk_wct_no

    #: 구매 정보2
    sale_info2 = None  # h_orgtk_ret_sale_dt

    #: 구매 정보3
    sale_info3 = None  # h_orgtk_sale_sqno

    #: 구매 정보4
    sale_info4 = None  # h_orgtk_ret_pwd

    #: 구매 가격
    price = None  # h_rcvd_amt  ex) 00013900

    def __init__(self, data):
        raw_data = data['ticket_list'][0]['train_info'][0]
        super(Ticket, self).__init__(raw_data)

        self.seat_no_end = _get_utf8(raw_data, 'h_seat_no_end')
        self.seat_no_count = int(_get_utf8(raw_data, 'h_seat_cnt'))

        self.buyer_name = _get_utf8(raw_data, 'h_buy_ps_nm')
        self.sale_date = _get_utf8(raw_data, 'h_orgtk_sale_dt')
        self.sale_info1 = _get_utf8(raw_data, 'h_orgtk_wct_no')
        self.sale_info2 = _get_utf8(raw_data, 'h_orgtk_ret_sale_dt')
        self.sale_info3 = _get_utf8(raw_data, 'h_orgtk_sale_sqno')
        self.sale_info4 = _get_utf8(raw_data, 'h_orgtk_ret_pwd')
        self.price = int(_get_utf8(raw_data, 'h_rcvd_amt'))

        self.car_no = _get_utf8(raw_data, 'h_srcar_no')
        self.seat_no = _get_utf8(raw_data, 'h_seat_no')

    def __repr__(self):
        repr_str = super(Train, self).__repr__()

        repr_str += " => %s호" % self.car_no

        if int(self.seat_no_count) != 1:
            repr_str += " %s~%s" % (self.seat_no, self.seat_no_end)
        else:
            repr_str += " %s" % self.seat_no

        repr_str += ", %s원" % self.price

        return repr_str

    def get_ticket_no(self):
        return "-".join(map(str, (self.sale_info1, self.sale_info2, self.sale_info3, self.sale_info4)))


class Passenger:
    """승객. Passenger List를 검색과 예약에 쓰도록 한다."""
    typecode = None  # txtPsgTpCd1    : '1',   #손님 종류 (어른 1, 어린이 3)
    discount_type = '000'  # txtDiscKndCd1  : '000', #할인 타입 (경로, 동반유아, 군장병 등..)
    count = 1  # txtCompaCnt1   : '1',   #인원수
    card = ''  # txtCardCode_1  : '',    #할인카드 종류
    card_no = ''  # txtCardNo_1    : '',    #할인카드 번호
    card_pw = ''  # txtCardPw_1    : '',    #할인카드 비밀번호

    @staticmethod
    def reduce(passenger_list):
        """Reduce passenger's list."""
        if list(filter(lambda x: not isinstance(x, Passenger), passenger_list)):
            raise TypeError("Passengers must be based on Passenger")

        groups = itertools.groupby(passenger_list, lambda x: x.group_key())
        return list(filter(lambda x: x.count > 0, [reduce(lambda a, b: a + b, g) for k, g in groups]))

    def __init__(self, *args, **kwargs):
        raise NotImplementedError("Passenger is abstract class. Do not make instance.")

    def __init_internal__(self, typecode, count=1, discount_type='000', card='', card_no='', card_pw=''):
        self.typecode = typecode
        self.count = count
        self.discount_type = discount_type
        self.card = card
        self.card_no = card_no
        self.card_pw = card_pw

    def __add__(self, other):
        assert isinstance(other, self.__class__)
        if self.group_key() == other.group_key():
            return self.__class__(count=self.count + other.count, discount_type=self.discount_type, card=self.card,
                                  card_no=self.card_no, card_pw=self.card_pw)
        else:
            raise TypeError(
                "other's group_key(%s) is not equal to self's group_key(%s)." % (other.group_key(), self.group_key()))

    def group_key(self):
        """get group string from attributes except count"""
        return "%s_%s_%s_%s_%s" % (self.typecode, self.discount_type, self.card, self.card_no, self.card_pw)

    def get_dict(self, index):
        assert isinstance(index, int)
        index = str(index)
        return {
            'txtPsgTpCd' + index: self.typecode,
            'txtDiscKndCd' + index: self.discount_type,
            'txtCompaCnt' + index: self.count,
            'txtCardCode_' + index: self.card,
            'txtCardNo_' + index: self.card_no,
            'txtCardPw_' + index: self.card_pw,
        }


# noinspection PyMissingConstructor
class AdultPassenger(Passenger):
    def __init__(self, count=1, discount_type='000', card='', card_no='', card_pw=''):
        Passenger.__init_internal__(self, '1', count, discount_type, card, card_no, card_pw)


# noinspection PyMissingConstructor
class ChildPassenger(Passenger):
    def __init__(self, count=1, discount_type='000', card='', card_no='', card_pw=''):
        Passenger.__init_internal__(self, '3', count, discount_type, card, card_no, card_pw)


# noinspection PyMissingConstructor
class ToddlerPassenger(Passenger):
    def __init__(self, count=1, discount_type='321', card='', card_no='', card_pw=''):
        Passenger.__init_internal__(self, '3', count, discount_type, card, card_no, card_pw)


# noinspection PyMissingConstructor
class SeniorPassenger(Passenger):
    def __init__(self, count=1, discount_type='131', card='', card_no='', card_pw=''):
        Passenger.__init_internal__(self, '1', count, discount_type, card, card_no, card_pw)


# noinspection PyMissingConstructor
class NCardPassenger(AdultPassenger):
    def __init__(self, count=1, card_no='', card='', card_pw='', discount_type=NCARD_DISCOUNT_CODE):
        AdultPassenger.__init__(self, count, discount_type, card, card_no, card_pw)


class TrainType:
    KTX = "100"  # "KTX, KTX-산천",
    SAEMAEUL = "101"  # "새마을호",
    MUGUNGHWA = "102"  # "무궁화호",
    TONGGUEN = "103"  # "통근열차",
    NURIRO = "102"  # "누리로",
    ALL = "109"  # "전체",
    AIRPORT = "105"  # "공항직통",
    KTX_SANCHEON = "100"  # "KTX-산천",
    ITX_SAEMAEUL = "101"  # "ITX-새마을",
    ITX_CHEONGCHUN = "104"  # "ITX-청춘",

    def __init__(self):
        raise NotImplementedError("Do not make instance.")


class ReserveOption:
    GENERAL_FIRST = "GENERAL_FIRST"  # 일반실 우선
    GENERAL_ONLY = "GENERAL_ONLY"  # 일반실만
    SPECIAL_FIRST = "SPECIAL_FIRST"  # 특실 우선
    SPECIAL_ONLY = "SPECIAL_ONLY"  # 특실만

    def __init__(self):
        raise NotImplementedError("Do not make instance.")


class Reservation(Train):
    """Revervation object"""

    # : 예약번호
    rsv_id = None  # h_pnr_no

    # : 여정 번호
    journey_no = None  # txtJrnySqno

    #: 여정 카운트
    journey_cnt = None  # txtJrnyCnt

    #: 예약변경 번호?
    rsv_chg_no = "00000"

    #: 자리 갯수
    seat_no_count = None  # h_tot_seat_cnt  ex) 001

    #: 결제 기한 날짜
    buy_limit_date = None  # h_ntisu_lmt_dt

    #: 결제 기한 시간
    buy_limit_time = None  # h_ntisu_lmt_tm

    #: 예약 가격
    price = None  # h_rsv_amt  ex) 00013900

    #: 열차 번호 (Not implemented)
    car_no = None  # h_srcar_no

    #: 자리 번호 (Not implemented)
    seat_no = None  # h_seat_no

    #: 자리 번호 (Not implemented)
    seat_no_end = None  # h_seat_no_end

    def __init__(self, data):
        super(Reservation, self).__init__(data)
        # 이 두 필드가 결과에 빠져있음
        self.dep_date = _get_utf8(data, 'h_run_dt')
        self.arr_date = _get_utf8(data, 'h_run_dt')

        self.rsv_id = _get_utf8(data, 'h_pnr_no')
        self.seat_no_count = int(_get_utf8(data, 'h_tot_seat_cnt'))
        self.buy_limit_date = _get_utf8(data, 'h_ntisu_lmt_dt')
        self.buy_limit_time = _get_utf8(data, 'h_ntisu_lmt_tm')
        self.price = int(_get_utf8(data, 'h_rsv_amt'))
        self.journey_no = _get_utf8(data, 'txtJrnySqno', "001")
        self.journey_cnt = _get_utf8(data, 'txtJrnyCnt', "01")
        self.rsv_chg_no = _get_utf8(data, 'hidRsvChgNo', "00000")


        # 좌석정보 추가 업데이트 필요.
        # self.car_no = None
        # self.seat_no = None
        # self.seat_no_end = None



    def __repr__(self):
        repr_str = super(Reservation, self).__repr__()

        repr_str += ", %s원(%s석)" % (self.price, self.seat_no_count)

        buy_limit_time = "%s:%s" % (self.buy_limit_time[:2], self.buy_limit_time[2:4])

        buy_limit_date = "%s월 %s일" % (int(self.buy_limit_date[4:6]), int(self.buy_limit_date[6:]))

        repr_str += ", 구입기한 %s %s" % (buy_limit_date, buy_limit_time)

        return repr_str


class ExceptionForm(type):
    codes = set()

    def __contains__(cls, item):
        return item in cls.codes


class KorailError(with_metaclass(ExceptionForm, Exception)):
    """Korail Base Error Class"""

    def __init__(self, msg, code):
        self.msg = msg
        self.code = code

    def __str__(self):
        return "%s (%s)" % (self.msg, self.code)


class NeedToLoginError(KorailError):
    """Korail NeedToLogin Error Class"""
    codes = {'P058'}

    def __init__(self, code=None):
        KorailError.__init__(self, "Need to Login", code)


class NoResultsError(KorailError):
    """Korail NoResults Error Class"""
    codes = {'P100',
             'WRG000000',
             'WRD000061',  # 직통열차는 없지만, 환승으로 조회 가능합니다.
             'WRT300005'
    }

    def __init__(self, code=None):
        KorailError.__init__(self, "No Results", code)


class SoldOutError(KorailError):
    codes = {'ERR211161'}

    def __init__(self, code=None):
        KorailError.__init__(self, "Sold out", code)


# noinspection PyUnresolvedReferences,PyRedeclaration
class Korail(object):
    """Korail object"""
    _session = None

    _device, _version = 'AD', '250601002'
    _sid_key = b"2485dd54d9deaa36"
    _device_id = "558a4f02041657ea"
    _key = 'korail1234567890'

    _idx = None

    membership_number = None
    name = None
    email = None

    def __init__(self, korail_id, korail_pw, auto_login=True, want_feedback=False):
        self._session = requests.session()
        self._session.headers.update({'User-Agent': DEFAULT_USER_AGENT})
        self._engine = DynaPathMasterEngine()
        self.korail_id = korail_id
        self.korail_pw = korail_pw
        self.want_feedback = want_feedback
        self.logined = False
        if auto_login:
            self.login(korail_id, korail_pw)

    def _generate_sid(self, ts):
        plaintext = (f"{self._device}{ts}").encode('utf-8')
        cipher = AES.new(self._sid_key, AES.MODE_CBC, iv=self._sid_key)
        return base64.b64encode(cipher.encrypt(pad(plaintext, 16))).decode('utf-8') + "\n"

    def _get_auth_headers_and_sid(self, url):
        headers = {}
        sid = None
        if any(path in url for path in DYNAPATH_PATHS):
            ts = int(time.time() * 1000)
            rand = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4))
            token = self._engine.generate_token(self._device_id, ts, rand)
            headers['x-dynapath-m-token'] = token
            sid = self._generate_sid(ts)
        return headers, sid

    def __enc_password(self, password):
        url = KORAIL_CODE
        data = {
            'code': "app.login.cphd"
        }

        r = self._session.post(url, data=data)
        j = json.loads(r.text)

        if j['strResult'] == 'SUCC' and j.get('app.login.cphd') is not None:
            self._idx = j['app.login.cphd']['idx']
            key = j['app.login.cphd']['key']

            encrypt_key = key.encode(encoding='utf-8', errors='strict')
            iv = key[:16].encode(encoding='utf-8', errors='strict')
            cipher = AES.new(encrypt_key, AES.MODE_CBC, iv)
            
            padded_data = pad(password.encode("utf-8"), AES.block_size)

            return base64.b64encode(base64.b64encode(cipher.encrypt(padded_data))).decode("utf-8")
        else:
            return False


    def login(self, korail_id=None, korail_pw=None):
        """Login to Korail server.
:param korail_id : `Korail membership number` or `phone number` or `email`
    membership   : xxxxxxxx (8 digits)
    phone number : xxx-xxxx-xxxx
    email        : xxx@xxx.xxx
:param korail_pw : Korail account korail_pw
:param auto_login=True :

First, you need to create a Korail object.

    >>> from korail2 import *
    >>> korail = Korail("12345678", YOUR_PASSWORD) # with membership number
    >>> korail = Korail("carpedm20@gmail.com", YOUR_PASSWORD) # with email
    >>> korail = Korail("010-9964-xxxx", YOUR_PASSWORD) # with phone number

If you do not want login automatically,

    >>> korail = Korail("12345678", YOUR_PASSWORD, auto_login=False)
    >>> korail.login()
    True

When you want change ID using existing object,

    >>> korail.login(ANOTHER_ID, ANOTHER_PASSWORD)
    True

"""
        if korail_id is None:
            korail_id = self.korail_id
        else:
            self.korail_id = korail_id

        if korail_pw is None:
            korail_pw = self.korail_pw
        else:
            self.korail_pw = korail_pw

        if EMAIL_REGEX.match(korail_id):
            txt_input_flg = '5'
        elif PHONE_NUMBER_REGEX.match(korail_id):
            txt_input_flg = '4'
        else:
            txt_input_flg = '2'

        url = KORAIL_LOGIN
        headers, sid = self._get_auth_headers_and_sid(url)

        data = {
            'Device': self._device,
            'Version': self._version, # HACK
            #'Version': self._version,
            # 2 : for membership number,
            # 4 : for phone number,
            # 5 : for email,
            'txtInputFlg': txt_input_flg,
            'txtMemberNo': korail_id,
            'txtPwd': self.__enc_password(korail_pw),
            'idx': self._idx
        }
        if sid:
            data['Sid'] = sid

        r = self._session.post(url, data=data, headers=headers)
        j = json.loads(r.text)

        if j['strResult'] == 'SUCC' and j.get('strMbCrdNo') is not None:
            self._key = j['Key']
            self.membership_number = j['strMbCrdNo']
            self.name = j['strCustNm']
            self.email = j['strEmailAdr']
            self.logined = True
            return True
        else:
            self.logined = False
            return False

    def logout(self):
        """Logout from Korail server"""
        url = KORAIL_LOGOUT
        self._session.get(url)
        self.logined = False

    def _result_check(self, j):
        """Result data check"""
        if self.want_feedback:
            print(j['h_msg_txt'])

        if j['strResult'] == 'FAIL':
            h_msg_cd = _get_utf8(j, 'h_msg_cd')
            h_msg_txt = _get_utf8(j, 'h_msg_txt')
            # P058 : 로그인 필요
            matched_error = list(filter(lambda x: h_msg_cd in x, (NoResultsError, NeedToLoginError, SoldOutError)))
            if matched_error:
                raise matched_error[0](h_msg_cd)
            else:
                raise KorailError(h_msg_txt, h_msg_cd)
        else:
            return True

    def search_train_allday(self, dep, arr, date=None, time=None, train_type=TrainType.ALL,
                            passengers=None, include_no_seats=False):
        """Search all trains for specific time and date."""
        min1 = timedelta(minutes=1)
        all_trains = []
        dep_time = time
        for i in range(15):  # 최대 15번 호출
            try:
                trains = self.search_train(dep, arr, date, dep_time, train_type, passengers, True)
                all_trains.extend(trains)
                # 만약 마지막 승차권의 출발시각이 23시 59분인 경우, 검색 중지. (다음 날 승차권 검색 방지)
                last_dep_time = datetime.strptime(all_trains[-1].dep_time, "%H%M%S")
                if (last_dep_time.hour == 23) & (last_dep_time.minute == 59):
                    break
                # 마지막 열차시간에 1분 더해서 계속 검색.
                t = last_dep_time + min1
                dep_time = t.strftime("%H%M%S")
            except NoResultsError:
                break

        if not include_no_seats:
            all_trains = list(filter(lambda x: x.has_seat(), all_trains))

        if len(all_trains) == 0:
            raise NoResultsError()

        return all_trains

    def search_train(self, dep, arr, date=None, time=None, train_type=TrainType.ALL,
                     passengers=None, include_no_seats=False, include_waiting_list=False):
        """Search trains for specific time and date.

:param dep: A departure station in Korean  ex) '서울'
:param arr: A arrival station in Korean  ex) '부산'
:param date: (optional) A departure date in `yyyyMMdd` format
:param time: (optional) A departure time in `hhmmss` format
:param train_type: (optional) A type of train
                   - 00: KTX, KTX-산천
                   - 01: 새마을호
                   - 02: 무궁화호
                   - 03: 통근열차
                   - 04: 누리로
                   - 05: 전체 (기본값)
                   - 06: 공학직통
                   - 07: KTX-산천
                   - 08: ITX-새마을
                   - 09: ITX-청춘
:param passengers=None: (optional) List of Passenger Objects. None means 1 AdultPassenger.
:param include_no_seats=False: (optional) When True, a result includes trains which has no seats.
:param include_waiting_list=False: (optional) When False, a result includes trains which has no seats but can make a wait reservation(예약 대기)'

Below is a sample usage of `search_train`:

    >>> dep = '서울'
    >>> arr = '동대구'
    >>> date = '20140815'
    >>> time = '144000'
    >>> trains = korail.search_train(dep, arr, date, time)
    [[KTX] 8월 3일, 서울~부산(11:00~13:42) 특실,일반실 예약가능,
     [ITX-새마을] 8월 3일, 서울~부산(11:04~16:00) 일반실 예약가능,
     [KTX] 8월 3일, 서울~부산(12:00~14:43) 특실,일반실 예약가능,
     [KTX] 8월 3일, 서울~부산(12:30~15:13) 특실,일반실 예약가능,
     [KTX] 8월 3일, 서울~부산(12:40~15:45) 특실,일반실 예약가능,
     [KTX] 8월 3일, 서울~부산(12:55~15:26) 특실,일반실 예약가능,
     [KTX] 8월 3일, 서울~부산(13:00~15:37) 특실,일반실 예약가능,
     [KTX] 8월 3일, 서울~부산(13:10~15:58) 특실,일반실 예약가능]

When you want to see trains which has no seats.

    >>> trains = korail.search_train(dep, arr, date, time, include_no_seats=True)
    [[KTX] 8월 3일, 서울~부산(11:00~13:42) 특실,일반실 예약가능,
     [ITX-새마을] 8월 3일, 서울~부산(11:04~16:00) 일반실 예약가능,
     [무궁화호] 8월 3일, 서울~부산(11:08~16:54) 입석 역발매중,
     [ITX-새마을] 8월 3일, 서울~부산(11:50~16:50) 입석 역발매중,
     [KTX] 8월 3일, 서울~부산(12:00~14:43) 특실,일반실 예약가능,
     [KTX] 8월 3일, 서울~부산(12:30~15:13) 특실,일반실 예약가능,
     [KTX] 8월 3일, 서울~부산(12:40~15:45) 특실,일반실 예약가능,
     [KTX] 8월 3일, 서울~부산(12:55~15:26) 특실,일반실 예약가능,
     [KTX] 8월 3일, 서울~부산(13:00~15:37) 특실,일반실 예약가능,
     [KTX] 8월 3일, 서울~부산(13:10~15:58) 특실,일반실 예약가능]

`passengers` is a list(or tuple) of Passeger Objects.
By this, you can search for multiple passengers.
There are 4 types of Passengers now, AdultPassenger, ChildPassenger, ToddlerPassenger and SeniorPassenger.

    # for 1 adult, 1 child, 1 toddler
    >>> psgrs = [AdultPassenger(), ChildPassenger(), ToddlerPassenger()]

    # for 2 adults, 1 child
    >>> psgrs = [AdultPassenger(2), ChildPassenger(1)]
    # ditto. They are being added each other by same group.
    >>> psgrs = [AdultPassenger(), AdultPassenger(), ChildPassenger()]

    # for 2 adults, 1 child, 1 senior
    >>> psgrs = [AdultPassenger(2), ChildPassenger(), SeniorPassenger()]

    # for 1 adult, It supports negative count or zero count.
    # But it uses passengers which the sum is greater than zero.
    >>> psgrs = [AdultPassenger(2), AdultPassenger(-1)]
    >>> psgrs = [AdultPassenger(), SeniorPassenger(0)]

    # Nothing
    >>> psgrs = [AdultPassenger(0), SeniorPassenger(0)]

    # then search or reserve train
    >>> trains = korail.search_train(dep, arr, date, time, passengers=psgrs)
    ...
    >>> korail.reserve(trains[0], psgrs)
    ...

"""
        # 코레일에 열차 티켓 리스트 API 요청시 한국시간을 기준으로 함.
        kst_now = datetime.utcnow() + timedelta(hours=9)
        if date is None:
            date = kst_now.strftime("%Y%m%d")
        if time is None:
            time = kst_now.strftime("%H%M%S")

        if passengers is None:
            passengers = [AdultPassenger()]

        passengers = Passenger.reduce(passengers)

        adult_count = reduce(lambda a, b: a + b.count, list(filter(lambda x: isinstance(x, AdultPassenger), passengers)), 0)
        child_count = reduce(lambda a, b: a + b.count, list(filter(lambda x: isinstance(x, ChildPassenger), passengers)), 0)
        toddler_count = reduce(lambda a, b: a + b.count, list(filter(lambda x: isinstance(x, ToddlerPassenger), passengers)), 0)
        senior_count = reduce(lambda a, b: a + b.count, list(filter(lambda x: isinstance(x, SeniorPassenger), passengers)), 0)

        url = KORAIL_SEARCH_SCHEDULE
        headers, sid = self._get_auth_headers_and_sid(url)
        data = {
            'Device': self._device,
            'radJobId': '1',
            'selGoTrain': train_type,
            'txtCardPsgCnt': '0',
            'txtGdNo': '',
            'txtGoAbrdDt': date,  # '20140803',
            'txtGoEnd': arr,
            'txtGoHour': time,  # '071500',
            'txtGoStart': dep,
            'txtJobDv': '',
            'txtMenuId': '11',
            'txtPsgFlg_1': adult_count,  # 어른
            'txtPsgFlg_2': child_count,  # 어린이
            'txtPsgFlg_8': toddler_count,  # 유아
            'txtPsgFlg_3': senior_count,  # 경로
            'txtPsgFlg_4': '0',  # 중증 장애인
            'txtPsgFlg_5': '0',  # 경증 장애인
            'txtSeatAttCd_2': '000',
            'txtSeatAttCd_3': '000',
            'txtSeatAttCd_4': '015',
            'txtTrnGpCd': train_type,

            'Version': self._version,
        }


        r = self._session.post(url, params=data, headers=headers)
        j = json.loads(r.text)

        if self._result_check(j):
            train_infos = j['trn_infos']['trn_info']

            trains = []

            for info in train_infos:
                trains.append(Train(info))

            filter_fns = [lambda x: x.has_seat()]

            if include_no_seats:
                filter_fns.append(lambda x: not x.has_seat())

            if include_waiting_list:
                filter_fns.append(lambda x: x.has_waiting_list())

            trains = list(filter(lambda x: any(f(x) for f in filter_fns), trains))

            if len(trains) == 0:
                raise NoResultsError()

            return trains

    def search_ncard_trains(self, dep, arr, dcnt_card_kind_mg_no, use_psb_tno,
                            date=None, time=None, train_type=TrainType.ALL,
                            dcnt_card_kind_cd="MMM", use_trm_dno="",
                            qry_pg_no="1", dirt_chtn_dv_cd="1"):
        """Search N-card discounted ticket train candidates.

        `dcnt_card_kind_mg_no` and `use_psb_tno` come from the user's owned
        N-card metadata in KorailTalk. This method only searches candidates; it
        does not reserve or pay for a ticket.
        """
        kst_now = datetime.utcnow() + timedelta(hours=9)
        if date is None:
            date = kst_now.strftime("%Y%m%d")
        if time is None:
            time = "000000"

        url = KORAIL_NCARD_SCHEDULE_VIEW
        headers, sid = self._get_auth_headers_and_sid(url)
        data = {
            'Device': self._device,
            'Version': self._version,
            'Key': self._key,
            'dptDt': date,
            'dptRsStnNm': dep,
            'arvRsStnNm': arr,
            'dptTm': time,
            'trnGpCd': train_type,
            'dirtChtnDvCd': dirt_chtn_dv_cd,
            'dcntCrdKndCd': dcnt_card_kind_cd,
            'dcntCrdKndMgNo': dcnt_card_kind_mg_no,
            'useTrmDno': use_trm_dno,
            'usePsbTno': use_psb_tno,
            'qryPgNo': qry_pg_no,
        }
        if sid:
            data['Sid'] = sid

        r = self._session.get(url, params=data, headers=headers)
        j = json.loads(r.text)

        if self._result_check(j):
            train_infos = (
                j.get('trnScdlList') or
                j.get('trn_scdl_list') or
                j.get('trn_infos', {}).get('trn_info') or
                []
            )
            if isinstance(train_infos, dict):
                train_infos = [train_infos]

            trains = [NCardTrain(info) for info in train_infos]
            if len(trains) == 0:
                raise NoResultsError()
            return trains

    def ncard_history(self, dcnt_card_no):
        """Return raw N-card usage history for an already known N-card number."""
        url = KORAIL_NCARD_USE_HISTORY
        headers, sid = self._get_auth_headers_and_sid(url)
        data = {
            'Device': self._device,
            'Version': self._version,
            'Key': self._key,
            'dcntCrdNo': dcnt_card_no,
        }
        if sid:
            data['Sid'] = sid

        r = self._session.get(url, params=data, headers=headers)
        j = json.loads(r.text)
        if self._result_check(j):
            return j

    def owned_ncards(self):
        """Return owned N-cards from KorailTalk's current-ticket list.

        KorailTalk shows purchased N-cards under "My Ticket > Commutation/Pass"
        using the same MyTicketList endpoint as ordinary tickets, then fetches
        details through SelTicketInfo. This method mirrors only that read-only
        lookup path.
        """
        list_data = {
            'Device': self._device,
            'Version': self._version,
            'Key': self._key,
            'txtDeviceId': '',
            'txtIndex': '1',
            'h_page_no': '1',
            'h_abrd_dt_from': '',
            'h_abrd_dt_to': '',
            'hiduserYn': 'Y',
            'hidName': '',
            'hidTeleNo': '',
            'hidPwd': '',
            'tsRsStnCd': '',
        }
        r = self._session.post(KORAIL_MYTICKETLIST, data=list_data)
        j = json.loads(r.text)

        try:
            self._result_check(j)
        except NoResultsError:
            return []

        ncards = []
        for reservation in j.get('reservation_list', []):
            ticket_list = reservation.get('ticket_list') or []
            if not ticket_list:
                continue
            train_info = ticket_list[0].get('train_info') or []
            if not train_info:
                continue
            ticket_data = train_info[0]
            ticket_kind = _get_utf8(ticket_data, 'h_tk_knd_nm') or ''
            if _get_utf8(ticket_data, 'h_tk_knd_cd') != '81' and 'N카드' not in ticket_kind:
                continue

            detail_data = {
                'Device': self._device,
                'Version': self._version,
                'Key': self._key,
                'h_orgtk_ret_sale_dt': _get_utf8(ticket_data, 'h_orgtk_ret_sale_dt'),
                'h_orgtk_wct_no': _get_utf8(ticket_data, 'h_orgtk_wct_no'),
                'h_orgtk_sale_sqno': _get_utf8(ticket_data, 'h_orgtk_sale_sqno'),
                'h_orgtk_ret_pwd': _get_utf8(ticket_data, 'h_orgtk_ret_pwd'),
                'h_purchase_history': '',
            }
            detail_response = self._session.post(KORAIL_MYTICKET_SEAT, data=detail_data)
            detail = json.loads(detail_response.text)
            try:
                self._result_check(detail)
            except KorailError:
                detail = {}
            ncards.append(NCard(ticket_data, detail))

        return ncards

    def _select_reservation_seat_type(self, train, option, try_waiting):
        reserving_seat = True
        seat_type = None
        try:
            if train.has_seat() is False:
                raise SoldOutError()
            elif option == ReserveOption.GENERAL_ONLY:
                if train.has_general_seat():
                    seat_type = '1'
                else:
                    raise SoldOutError()
            elif option == ReserveOption.SPECIAL_ONLY:
                if train.has_special_seat():
                    seat_type = '2'
                else:
                    raise SoldOutError()
            elif option == ReserveOption.GENERAL_FIRST:
                if train.has_general_seat():
                    seat_type = '1'
                else:
                    seat_type = '2'
            elif option == ReserveOption.SPECIAL_FIRST:
                if train.has_special_seat():
                    seat_type = '2'
                else:
                    seat_type = '1'
        except SoldOutError as e:
            if try_waiting and option != ReserveOption.SPECIAL_ONLY and train.has_general_waiting_list():
                reserving_seat = False
                seat_type = '1'
            else:
                raise e
        return reserving_seat, seat_type

    def _build_reservation_data(self, train, passengers=None,
                                option=ReserveOption.GENERAL_FIRST,
                                try_waiting=False):
        reserving_seat, seat_type = self._select_reservation_seat_type(train, option, try_waiting)

        if passengers is None:
            passengers = [AdultPassenger()]

        passengers = Passenger.reduce(passengers)
        cnt = reduce(lambda x, y: x + y.count, passengers, 0)
        data = {
            'Device': self._device,
            'Version': self._version,
            'Key': self._key,
            'txtGdNo': '',
            'txtJobId': '1101' if reserving_seat else '1102',
            'txtTotPsgCnt': cnt,
            'txtSeatAttCd1': '000',
            'txtSeatAttCd2': '000',
            'txtSeatAttCd3': '000',
            'txtSeatAttCd4': '015',
            'txtSeatAttCd5': '000',
            'hidFreeFlg': 'N',
            'txtStndFlg': 'N',
            'txtMenuId': '11',
            'txtSrcarCnt': '0',
            'txtJrnyCnt': '1',

            # 이하 여정정보1
            'txtJrnySqno1': '001',
            'txtJrnyTpCd1': '11',
            'txtDptDt1': train.dep_date,
            'txtDptRsStnCd1': train.dep_code,
            'txtDptTm1': train.dep_time,
            'txtArvRsStnCd1': train.arr_code,
            'txtTrnNo1': train.train_no,
            'txtRunDt1': train.run_date,
            'txtTrnClsfCd1': train.train_type,
            'txtPsrmClCd1': seat_type,
            'txtTrnGpCd1': train.train_group,
            'txtChgFlg1': '',

            # 이하 여정정보2
            'txtJrnySqno2': '',
            'txtJrnyTpCd2': '',
            'txtDptDt2': '',
            'txtDptRsStnCd2': '',
            'txtDptTm2': '',
            'txtArvRsStnCd2': '',
            'txtTrnNo2': '',
            'txtRunDt2': '',
            'txtTrnClsfCd2': '',
            'txtPsrmClCd2': '',
            'txtChgFlg2': '',
        }

        index = 1
        for psg in passengers:
            data.update(psg.get_dict(index))
            index += 1
        return data

    def build_ncard_reservation_payload(self, train, ncard_no,
                                        option=ReserveOption.GENERAL_FIRST,
                                        try_waiting=False):
        """Build, but do not submit, an N-card discounted reservation payload."""
        passengers = [NCardPassenger(card_no=ncard_no)]
        return self._build_reservation_data(train, passengers, option, try_waiting)

    def reserve(self, train, passengers=None, option=ReserveOption.GENERAL_FIRST, try_waiting=False):
        """Reserve a train.

:param train: An instance of `Train`.
:param passengers=None: (optional) List of Passenger Objects. None means 1 AdultPassenger.
:param option=ReserveOption.GENERAL_FIRST : (optional)

When tickets are not enough much for passengers, it raises SoldOutError.

If you want to select priority of seat grade, general or special,
There are 4 options in ReserveOption class.

- GENERAL_FIRST : Economic than Comfortable.
- GENERAL_ONLY  : Reserve only general seats. You are poorman ;-)
- SPECIAL_FIRST : Comfortable than Economic.
- SPECIAL_ONLY  : Richman.

:param option=try_waiting : (optional)

When the train allows waiting, enroll for the waiting list instead of failing in case there are no seats in the train.

        """

        print(train)

        url = KORAIL_TICKETRESERVATION
        headers, sid = self._get_auth_headers_and_sid(url)
        data = self._build_reservation_data(train, passengers, option, try_waiting)

        r = self._session.get(url, params=data, headers=headers)
        j = json.loads(r.text)
        if self._result_check(j):
            rsv_id = j['h_pnr_no']
            rsvlist = list(filter(lambda x: x.rsv_id == rsv_id, self.reservations()))
            if len(rsvlist) == 1:
                return rsvlist[0]

    def tickets(self):
        """Get list of tickets"""
        url = KORAIL_MYTICKETLIST
        data = {
            'Device': self._device,
            'Version': self._version,
            'Key': self._key,
            'txtIndex': '1',
            'h_page_no': '1',
            'txtDeviceId': '',
            'h_abrd_dt_from': '',
            'h_abrd_dt_to': '',
        }

        r = self._session.get(url, params=data)
        j = json.loads(r.text)
        try:
            if self._result_check(j):
                ticket_infos = j['reservation_list']

                tickets = []

                for info in ticket_infos:
                    ticket = Ticket(info)
                    url = KORAIL_MYTICKET_SEAT
                    data = {
                        'Device': self._device,
                        'Version': self._version,
                        'Key': self._key,
                        'h_orgtk_wct_no': ticket.sale_info1,
                        'h_orgtk_ret_sale_dt': ticket.sale_info2,
                        'h_orgtk_sale_sqno': ticket.sale_info3,
                        'h_orgtk_ret_pwd': ticket.sale_info4,
                    }
                    r = self._session.get(url, params=data)
                    j = json.loads(r.text)
                    if self._result_check(j):
                        seat = j['ticket_infos']['ticket_info'][0]['tk_seat_info'][0]
                        ticket.seat_no = _get_utf8(seat, 'h_seat_no')
                        ticket.seat_no_end = None

                    tickets.append(ticket)

                return tickets
        except NoResultsError:
            return []

    def reservations(self):
        """ Get My Reservations """
        url = KORAIL_MYRESERVATIONLIST
        data = {
            'Device': self._device,
            'Version': self._version,
            'Key': self._key,
        }
        r = self._session.get(url, params=data)
        j = json.loads(r.text)
        try:
            if self._result_check(j):
                rsv_infos = j['jrny_infos']['jrny_info']

                reserves = []

                for info in rsv_infos:
                    for tinfo in info['train_infos']['train_info']:
                        reserves.append(Reservation(tinfo))
                return reserves
        except NoResultsError:
            return []

    def cancel(self, rsv):
        """ Cancel Reservation : Canceling is for reservation, for ticket would be Refunding """
        assert isinstance(rsv, Reservation)
        url = KORAIL_CANCEL
        data = {
            'Device': self._device,
            'Version': self._version,
            'Key': self._key,
            'txtPnrNo': rsv.rsv_id,
            'txtJrnySqno': rsv.journey_no,
            'txtJrnyCnt': rsv.journey_cnt,
            'hidRsvChgNo': rsv.rsv_chg_no,
        }
        r = self._session.get(url, data=data)
        j = json.loads(r.text)
        if self._result_check(j):
            return True
