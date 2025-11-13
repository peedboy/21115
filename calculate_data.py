import pandas as pd
import numpy as np
import math

# === 파일 리스트 ===
files = [
    "./고정형 2칸/mpu6050_20251112_041209.csv",
    "./고정형 2칸/mpu6050_20251112_041241.csv",
    "./고정형 2칸/mpu6050_20251112_041320.csv",
    "./0칸/mpu6050_20251112_030956.csv",
    "./0칸/mpu6050_20251112_031144.csv",
    "./0칸/mpu6050_20251112_031321.csv",
    "./1칸/mpu6050_20251112_032536.csv",
    "./1칸/mpu6050_20251112_032846.csv",
    "./1칸/mpu6050_20251112_032917.csv",
    "./2칸/mpu6050_20251112_034326.csv",
    "./2칸/mpu6050_20251112_034414.csv",
    "./2칸/mpu6050_20251112_034444.csv",
    "./3칸/mpu6050_20251112_034756.csv",
    "./3칸/mpu6050_20251112_034839.csv",
    "./3칸/mpu6050_20251112_034927.csv"
]

# === 계산 함수 ===
def analyze_file(file_path):
    df = pd.read_csv(file_path)

    # 숫자형 변환
    for col in ["aY", "aZ", "gX", "time(s)"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["aY", "aZ", "gX", "time(s)"])
    df["dt"] = df["time(s)"].diff().fillna(0)

    # 각도 계산
    theta = []
    for i in range(len(df)):
        aY, aZ = df["aY"].iloc[i], df["aZ"].iloc[i]
        try:
            part1 = 9.8 / math.sqrt(aY**2 + aZ**2)
            part1 = max(min(part1, 1), -1)
            t = math.asin(part1) - math.atan2(aZ, aY)
        except:
            t = 0
        theta.append(t)
    df["theta"] = theta

    # 중력 보정
    g = 9.8
    df["aY_corr"] = df["aY"] - g * np.sin(df["theta"])
    df["aZ_corr"] = df["aZ"] - g * np.cos(df["theta"])

    # 속도 적분
    vY, vZ = [0], [0]
    for i in range(1, len(df)):
        vY.append(vY[-1] + df["aY_corr"].iloc[i] * df["dt"].iloc[i])
        vZ.append(vZ[-1] + df["aZ_corr"].iloc[i] * df["dt"].iloc[i])
    df["vY"], df["vZ"] = vY, vZ

    # 이동거리 계산식 수정 (절대좌표 변환)
    df["displacement_y"] = np.abs(
        np.sqrt((df["vY"] * np.sin(df["theta"]))**2 + (df["vZ"] * np.cos(df["theta"]))**2) * df["dt"]
    )
    total_displacement_y = df["displacement_y"].sum()

    # 회전수 계산
    df["g_rad_s"] = np.deg2rad(df["gX"])
    rotation = np.sum(np.abs(df["g_rad_s"] * df["dt"])) / (2 * np.pi)

    return total_displacement_y, rotation

# === 실행 ===
results = []
for file_path in files:
    try:
        dist, rot = analyze_file(file_path)
        folder_name = file_path.split("/")[1] if "/" in file_path else "기타"
        results.append({"폴더": folder_name, "파일명": file_path.split("/")[-1],
                        "y축 이동거리(m)": dist, "회전수(바퀴)": rot})
    except Exception as e:
        print(f"{file_path} 처리 오류:", e)

df_results = pd.DataFrame(results)
if len(df_results) > 0:
    folder_avg = df_results.groupby("폴더")[["y축 이동거리(m)", "회전수(바퀴)"]].mean().reset_index()

    print("\n=== 개별 파일 결과 ===")
    print(df_results.round(4))

    print("\n=== 폴더별 평균 결과 ===")
    print(folder_avg.round(4))
else:
    print("모든 파일에서 오류 발생. CSV 확인 필요.")
