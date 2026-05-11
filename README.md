
Legal disclaimer
---

**Usage of korail for attacking targets without prior mutual consent is illegal**. It's the end user's responsibility to obey all applicable local, state and federal laws. Developers assume no liability and are not responsible for any misuse or damage caused by this program. Only use for educational purposes.


<br/>

Korail2 (with N-card discount support)
=======================================

A fork of [korail2](https://github.com/carpedm20/korail2) with added support for **KorailTalk N-card discounted tickets**.

The original korail2 project appears to be no longer actively maintained, so this fork was created to keep the library working with the current Korail API and to add N-card discount functionality.

Added on top of the original project:
- Query owned N-cards (`owned_ncards`)
- Search discounted trains with an owned N-card (`search_owned_ncard_trains`)
- Build N-card reservation payload (`build_ncard_reservation_payload`)
- N-card usage history (`ncard_history`)
- KorailTalk dynamic auth token generation (`DynaPathMasterEngine`)
- AES-encrypted login


Installing
----------

Install from PyPI:

    $ pip install korail2-ncard pycryptodome

Or install from source:

    $ git clone https://github.com/ce-dric/korail2.git
    $ cd korail2
    $ pip install -e .


Using
-----

### 1. Login ###

First, you need to create a Korail object.

```python
>>> from korail2 import *
>>> korail = Korail("12345678", YOUR_PASSWORD)          # with membership number
>>> korail = Korail("example@email.com", YOUR_PASSWORD) # with email
>>> korail = Korail("010-9964-xxxx", YOUR_PASSWORD)     # with phone number
```

If you do not want login automatically,

```python
>>> korail = Korail("12345678", YOUR_PASSWORD, auto_login=False)
>>> korail.login()
True
```

When you want to change ID using an existing object,

```python
>>> korail.login(ANOTHER_ID, ANOTHER_PASSWORD)
True
```

### 2. Search train ###

You can search train schedules with `search_train` and `search_train_allday` methods.

- `search_train` returns up to 10 results. Faster than `search_train_allday`.
- `search_train_allday` returns all results after the given time. Calls `search_train` repeatedly.

Both methods take these arguments:

- `dep` : A departure station in Korean  ex) `'서울'`
- `arr` : An arrival station in Korean  ex) `'부산'`
- `date` : (optional) A departure date in `yyyyMMdd` format
- `time` : (optional) A departure time in `hhmmss` format
- `train_type`: (optional) A type of train. Use `TrainType` class constants. Default: `TrainType.ALL`.
    - `TrainType.KTX` — KTX / KTX-산천
    - `TrainType.SAEMAEUL` — 새마을호 / ITX-새마을
    - `TrainType.MUGUNGHWA` — 무궁화호
    - `TrainType.NURIRO` — 누리로
    - `TrainType.ITX_CHEONGCHUN` — ITX-청춘
    - `TrainType.AIRPORT` — 공항직통
    - `TrainType.ALL` — all types
- `passengers`: (optional) List of Passenger objects. `None` means 1 `AdultPassenger`.
- `include_no_seats`: (optional) When `True`, results include sold-out trains.

```python
>>> dep = '서울'
>>> arr = '동대구'
>>> date = '20260512'
>>> time = '100000'
>>> trains = korail.search_train(dep, arr, date, time)
[[KTX] 5월 12일, 서울~동대구(10:00~11:43) 특실,일반실 예약가능,
 [KTX] 5월 12일, 서울~동대구(10:30~12:05) 특실,일반실 예약가능,
 ...]
```

#### 2-1. About the `passengers` argument

`passengers` is a list (or tuple) of Passenger objects. Supported types:

- `AdultPassenger` — adult
- `ChildPassenger` — child
- `ToddlerPassenger` — toddler (동반유아 discount)
- `SeniorPassenger` — senior (경로 discount)
- `NCardPassenger` — N-card discount (see N-card section below)

```python
# 1 adult, 1 child
>>> psgrs = [AdultPassenger(), ChildPassenger()]

# 2 adults, 1 child
>>> psgrs = [AdultPassenger(2), ChildPassenger(1)]

# 2 adults, 1 child, 1 senior
>>> psgrs = [AdultPassenger(2), ChildPassenger(), SeniorPassenger()]

# 1 adult, 1 toddler
>>> psgrs = [AdultPassenger(), ToddlerPassenger()]

# then search or reserve
>>> trains = korail.search_train(dep, arr, date, time, passengers=psgrs)
>>> korail.reserve(trains[0], psgrs)
```

### 3. Make a reservation ###

```python
>>> trains = korail.search_train(dep, arr, date, time)
>>> seat = korail.reserve(trains[0])
>>> seat
[KTX] 5월 12일, 서울~동대구(10:00~11:43) 42500원(1석), 구입기한 5월 8일 14:05
```

Multiple passengers:

```python
>>> seat = korail.reserve(trains[0], passengers=psgrs)
```

If seats are not available for the number of passengers, `SoldOutError` is raised.

To select seat grade priority, use `ReserveOption`:

- `GENERAL_FIRST` — economy before first class (default)
- `GENERAL_ONLY` — economy only
- `SPECIAL_FIRST` — first class before economy
- `SPECIAL_ONLY` — first class only

```python
>>> korail.reserve(trains[0], psgrs, ReserveOption.GENERAL_ONLY)
```

To join the waiting list when sold out:

```python
>>> korail.reserve(trains[0], psgrs, try_waiting=True)
```

#### 3-1. N-card discounted tickets ####

N-card support is based on static analysis of the KorailTalk Android API. Payment automation is out of scope — this library covers train search and reservation payload construction only.

**List owned N-cards:**

```python
>>> cards = korail.owned_ncards()
>>> cards[0]
[N카드] 대전~서울 0012345678-20260101-001-1234
>>> cards[0].discount_card_no
'1234567890123456'
```

**Search discounted trains with an owned N-card** (mirrors KorailTalk "My Ticket > Pass > N-card > Ticket booking"):

```python
>>> trains = korail.search_owned_ncard_trains(
...     cards[0],
...     dep='대전',
...     arr='서울',
...     date='20260512',
...     time='100000',
...     train_type=TrainType.KTX,
... )
>>> trains[0]
[KTX] 대전~서울(10:00~10:57) 9900원 15%할인
>>> trains[0].discount_name
'15%할인'
>>> trains[0].general_remaining_seats
'023'
```

**Build a reservation payload** (complete final payment in the official app/website):

```python
>>> payload = korail.build_ncard_reservation_payload(
...     trains[0],
...     ncard_no=cards[0].discount_card_no,
... )
>>> payload['txtDiscKndCd1']
'153'
```

If Korail only allows immediate payment/issuance for a discounted ticket, complete the final step in the official app or website.

**N-card usage history:**

```python
>>> history = korail.ncard_history(cards[0].discount_card_no)
```

**`search_ncard_trains`** is retained for N-card kind/product schedule research when you already have the raw card metadata. For booking with owned cards, prefer `search_owned_ncard_trains`.

### 4. Show reservations ###

```python
>>> reservations = korail.reservations()
>>> reservations
[[KTX] 5월 12일, 서울~동대구(10:00~11:43) 42500원(1석), 구입기한 5월 8일 14:03,
 [무궁화호] 5월 12일, 서울~동대구(10:30~14:15) 21100원(1석), 구입기한 5월 8일 14:03]
```

### 5. Cancel reservation ###

```python
>>> korail.cancel(reservations[0])
```

### 6. Get tickets already paid ###

```python
>>> korail = Korail("12345678", YOUR_PASSWORD, want_feedback=True)
>>> tickets = korail.tickets()
>>> print(tickets)
[[KTX] 5월 10일, 동대구~울산(09:26~09:54) => 5호 4A, 13900원]
```


Todo
----

1. N-card payment API (currently payload construction only)


License
-------

Source codes are distributed under BSD license.


Credits
-------

Based on [korail2](https://github.com/carpedm20/korail2) by:
- Taehoon Kim / [@carpedm20](http://carpedm20.github.io/about/)
- Hanson Kim / [@sng2c](https://github.com/sng2c)

N-card discount support and maintenance:
- Changwoo Song / [@ce-dric](https://github.com/ce-dric)
