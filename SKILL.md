---
name: ktx-booking
description: Search, reserve, inspect, and cancel KTX or Korail tickets in Korea with the korail2-ncard + pycryptodome Python packages. Use when the user asks for KTX seats, Korail bookings, train changes, reservation status, or N-card discounted tickets.
license: BSD
---

# KTX Booking

## What this skill does

`korail2-ncard` 위에 `scripts/ktx_booking.py` helper 를 얹어 KTX/Korail 조회, 예약, 예약 확인, 취소, N카드 할인 예매를 처리한다.

## When to use

- "서울에서 부산 가는 KTX 찾아줘"
- "코레일 예약 확인해줘"
- "KTX 취소해줘"
- "오전 9시 이후 KTX 중 제일 빠른 거 잡아줘"
- "N카드로 할인 열차 찾아줘"
- "내 N카드 목록 보여줘"
- "N카드 할인 적용해서 예약해줘"

## When not to use

- SRT 예매인 경우
- 실결제 확정까지 자동화해야 하는 경우
- credential 을 평문으로 넣으려는 경우

## Prerequisites

- Python 3.10+
- `python3 -m pip install korail2-ncard pycryptodome`

## Required environment variables

- `KSKILL_KTX_ID`
- `KSKILL_KTX_PASSWORD`

### Credential resolution order

1. **이미 환경변수에 있으면** 그대로 사용한다.
2. **에이전트가 자체 secret vault(1Password CLI, Bitwarden CLI, macOS Keychain 등)를 사용 중이면** 거기서 꺼내 환경변수로 주입해도 된다.
3. **`~/.config/k-skill/secrets.env`** (기본 fallback) — plain dotenv 파일, 퍼미션 `0600`.
4. **아무것도 없으면** 유저에게 물어서 2 또는 3에 저장한다.

## Workflow

### 0. Install the package when missing

```bash
python3 -m pip install korail2-ncard pycryptodome
```

### 1. Search trains

```bash
python3 scripts/ktx_booking.py search 서울 부산 20260328 090000 --limit 5
```

### 2. Reserve

```bash
python3 scripts/ktx_booking.py reserve 서울 부산 20260328 090000 --train-id <train_id> --seat-option general-first
```

### 3. N-card discounted reservation

```bash
# 보유 N카드 목록 조회
python3 scripts/ktx_booking.py ncard-list

# N카드 할인 열차 조회
python3 scripts/ktx_booking.py ncard-search 대전 서울 20260512 100000 --ncard-index 1

# N카드로 예약
python3 scripts/ktx_booking.py reserve 대전 서울 20260512 100000 \
  --train-id <train_id> \
  --ncard-no <card_no>
```

### 4. Inspect / cancel

```bash
python3 scripts/ktx_booking.py reservations
python3 scripts/ktx_booking.py cancel <reservation_id>
```

## Notes

- 결제 완료까지는 자동화하지 않는다
- `scripts/ktx_booking.py` is based on [NomaDamas/k-skill](https://github.com/NomaDamas/k-skill) (MIT License)
