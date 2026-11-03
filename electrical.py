import argparse
import csv
import math
from datetime import datetime
from pathlib import Path


CSV_FIELDS = (
    "timestamp",
    "voltage_v",
    "current_a",
    "power_factor",
    "power_w",
    "duration_hours",
    "energy_kwh",
    "threshold_w",
    "over_limit",
)


def calculate_reading(
    voltage_v: float,
    current_a: float,
    power_factor: float = 1.0,
    duration_hours: float = 1.0,
    threshold_w: float = 1000.0,
) -> dict:
    """Calculate power and energy for one voltage/current measurement."""
    values = (voltage_v, current_a, power_factor, duration_hours, threshold_w)
    if not all(math.isfinite(value) for value in values):
        raise ValueError("ค่าที่ป้อนต้องเป็นตัวเลขที่ไม่ใช่ infinity หรือ NaN")
    if voltage_v < 0 or current_a < 0:
        raise ValueError("แรงดันและกระแสต้องไม่ติดลบ")
    if not 0 <= power_factor <= 1:
        raise ValueError("power factor ต้องอยู่ระหว่าง 0 ถึง 1")
    if duration_hours < 0 or threshold_w < 0:
        raise ValueError("ระยะเวลาและค่าขีดจำกัดต้องไม่ติดลบ")

    power_w = voltage_v * current_a * power_factor
    return {
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "voltage_v": voltage_v,
        "current_a": current_a,
        "power_factor": power_factor,
        "power_w": power_w,
        "duration_hours": duration_hours,
        "energy_kwh": power_w * duration_hours / 1000,
        "threshold_w": threshold_w,
        "over_limit": power_w > threshold_w,
    }


def append_reading(path: str | Path, reading: dict) -> None:
    """Append a reading to a CSV file, adding a header for a new file."""
    csv_path = Path(path)
    write_header = not csv_path.exists() or csv_path.stat().st_size == 0
    with csv_path.open("a", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow(reading)


def analyze_dc(voltage_v: float, resistance_ohm: float) -> dict:
    """Calculate current and power for a DC circuit using Ohm's law."""
    if not math.isfinite(voltage_v) or not math.isfinite(resistance_ohm):
        raise ValueError("แรงดันและความต้านทานต้องเป็นตัวเลขที่ไม่ใช่ infinity หรือ NaN")
    if voltage_v < 0:
        raise ValueError("แรงดันต้องไม่ติดลบ")
    if resistance_ohm <= 0:
        raise ValueError("ความต้านทานต้องมากกว่า 0 โอห์ม")

    current_a = voltage_v / resistance_ohm
    power_w = voltage_v * current_a
    return {"current_a": current_a, "power_w": power_w}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="คำนวณกำลังไฟฟ้า พลังงาน และบันทึกผลลง CSV"
    )
    parser.add_argument("--voltage", type=float, help="แรงดันไฟฟ้า (V)")
    parser.add_argument("--current", type=float, help="กระแสไฟฟ้า (A)")
    parser.add_argument(
        "--power-factor", type=float, default=1.0, help="Power factor (0-1, default: 1)"
    )
    parser.add_argument(
        "--duration-hours", type=float, default=1.0, help="ช่วงเวลาที่คำนวณ (ชั่วโมง)"
    )
    parser.add_argument(
        "--threshold-w", type=float, default=1000.0, help="ค่ากำลังไฟสำหรับแจ้งเตือน (W)"
    )
    parser.add_argument(
        "--log", default="energy_log.csv", help="ไฟล์ CSV สำหรับบันทึก (default: energy_log.csv)"
    )
    args = parser.parse_args()

    try:
        voltage_v = args.voltage
        current_a = args.current
        if voltage_v is None:
            voltage_v = float(input("ป้อนแรงดันไฟฟ้า (V): "))
        if current_a is None:
            current_a = float(input("ป้อนกระแสไฟฟ้า (A): "))
        reading = calculate_reading(
            voltage_v,
            current_a,
            args.power_factor,
            args.duration_hours,
            args.threshold_w,
        )
        append_reading(args.log, reading)
    except (OSError, ValueError) as error:
        parser.error(str(error))

    print(f"แรงดัน: {reading['voltage_v']:.2f} V")
    print(f"กระแส: {reading['current_a']:.2f} A")
    print(f"กำลังไฟ: {reading['power_w']:.2f} W")
    print(f"พลังงานในช่วงนี้: {reading['energy_kwh']:.4f} kWh")
    print("สถานะ: เกินค่ากำหนด!" if reading["over_limit"] else "สถานะ: ปกติ")
    print(f"บันทึกแล้ว: {args.log}")


if __name__ == "__main__":
    main()