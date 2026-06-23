# CHESS Monitoring

CHESS Monitoring은 크린룸 하이브리드 에너지 절감 제어 시스템(CHESS)의 실증 데이터를 수집하고 저장하기 위한 모니터링 모듈입니다.

이 저장소의 목표는 CHESS가 제어한 결과를 시계열 데이터로 남겨서 다음 항목을 검증하는 것입니다.

- CO₂ 기반 환기 수요 변화
- AHU 팬 인버터 주파수 변화
- 외기 댐퍼 개도율 변화
- 순간 전력 및 누적 전력량 변화
- Fan Law 기반 이론 절감율과 실측 전력의 차이
- 차압, 입자 농도, 온습도 등 크린룸 안전 조건 유지 여부

## 현재 구현 범위

`dev` 브랜치에는 1차 데이터 수집 코드가 들어 있습니다.

지원 기능:

- YAML 설정 기반 수집기 실행
- Simulated source를 이용한 개발용 가상 데이터 생성
- HTTP JSON gateway에서 센서 데이터 수집
- CSV replay를 이용한 테스트 데이터 재생
- CSV 파일 저장
- Fan Law 기반 이론 전력 잔존율 자동 계산
- 기본 범위 검증 및 알람 코드 기록

## 빠른 실행

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python -m chess_monitoring.cli --config config.example.yaml --once --print-json
```

지속 수집:

```bash
python -m chess_monitoring.cli --config config.example.yaml
```

수집 결과는 기본적으로 아래 파일에 저장됩니다.

```text
data/chess_measurements.csv
```

## 데이터 구조

주요 필드는 다음과 같습니다.

| 필드 | 설명 |
|---|---|
| `timestamp` | 측정 시각 |
| `site_id` | 현장 ID |
| `ahu_id` | AHU ID |
| `co2_ppm` | 실내 CO₂ 농도 |
| `outdoor_co2_ppm` | 외기 CO₂ 농도 |
| `temperature_c` | 실내 온도 |
| `relative_humidity_pct` | 상대습도 |
| `differential_pressure_pa` | 차압 |
| `particle_count` | 입자 농도 |
| `damper_position_pct` | 외기 댐퍼 개도율 |
| `fan_frequency_hz` | 팬 인버터 주파수 |
| `fan_speed_pct` | 기준 속도 대비 팬 속도 |
| `fan_law_power_ratio` | Fan Law 기반 이론 전력 잔존율 |
| `power_kw` | 순간 전력 |
| `energy_kwh` | 누적 전력량 |
| `operation_mode` | baseline/control/alarm 등 운전 모드 |
| `alarm_code` | 알람 코드 |

## 브랜치 운영

- `main`: 문서 및 안정 버전
- `dev`: 수집 코드 개발 브랜치

## 관련 문서

- [CHESS 연계 문서](docs/chess-integration.md)
- [데이터 수집 설계](docs/data-collection.md)
