<div align="center">

# 🔵 BLE Device Emulator & Client

### Универсальная платформа для эмуляции и тестирования BLE-устройств

![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-blue)
![.NET](https://img.shields.io/badge/.NET-8.0-purple)
![Python](https://img.shields.io/badge/Python-3.10+-green)
![BLE](https://img.shields.io/badge/BLE-5.0+-orange)
![License](https://img.shields.io/badge/license-MIT-yellow)
![Status](https://img.shields.io/badge/status-stable-brightgreen)

[🚀 Быстрый старт](#-быстрый-старт) • [📖 Документация](#-документация) • [🐛 FAQ](#-faq) • [🤝 Contributing](#-contributing)

</div>

---

## 📋 О проекте

Платформа из двух компонентов, превращающая обычный Windows-ПК в полноценный полигон для тестирования BLE-устройств:

- **🖥️ BleEmulator** (C# / .NET 8) — BLE-сервер, эмулирующий 8 типов устройств
- **💻 ble_client** (Python / PyQt6) — десктопный клиент с графиками, медиаплеером и интеграцией в умный дом

> 💡 **Идея:** запустить эмулятор на одном ноутбуке, а клиентом подключиться с другого — и получить полноценную систему "умный дом" без покупки реальных устройств.

---

## 🎯 Возможности

### Эмулятор (C#)
- ✅ 8 типов BLE-устройств из коробки
- ✅ Поддержка **Notify**, **Read**, **Write** операций
- ✅ Кастомные имена устройств (телефон видит как реальное)
- ✅ Аутентификация (PIN-код для замка)
- ✅ Двусторонняя связь (команды от клиента)

### Клиент (Python)
- ✅ 📊 Графики в реальном времени (pyqtgraph)
- ✅ 🎯 Круговые индикаторы (gauge)
- ✅ 🎬 Медиаплеер для аудио/видео
- ✅ 📁 Экспорт данных в **CSV**
- ✅ 📸 Сохранение графиков в **PNG**
- ✅ 🏠 Интеграция с **Home Assistant** через MQTT
- ✅ 🔔 Системные уведомления Windows
- ✅ 🎨 Тёмная тема

---

## 🏗️ Архитектура
## Архитектура системы

```mermaid
flowchart LR
    subgraph SERVER["💻 Ноутбук 1 — Сервер"]
        BE["BleEmulator<br/>(C#)"]
        
        H10["💓 Polar H10"]
        META["🕶️ Ray-Ban Meta"]
        TEMP["🌡️ Xiaomi Temp"]
        AIRPODS["🎧 AirPods Pro"]
        KICKR["🚴 Wahoo KICKR"]
        WATCH["⌚ Galaxy Watch"]
        YEELIGHT["💡 Yeelight Bulb"]
        AQARA["🔒 Aqara Lock"]

        BE --- H10
        BE --- META
        BE --- TEMP
        BE --- AIRPODS
        BE --- KICKR
        BE --- WATCH
        BE --- YEELIGHT
        BE --- AQARA
    end

    BLE["📡 BLE 5.0<br/>Advertising • GATT Notify<br/>GATT Write • GATT Read"]

    subgraph CLIENT["💻 Ноутбук 2 — Клиент"]
        PY["ble_client<br/>(Python)"]
        
        GRAPHS["📊 Графики"]
        GAUGE["🎯 Gauge"]
        PLAYER["🎬 Плеер"]
        CSV["📁 CSV экспорт"]
        PNG["📸 PNG экспорт"]
        MQTT["🏠 MQTT → HA"]
        NOTIFY["🔔 Уведомления"]

        PY --- GRAPHS
        PY --- GAUGE
        PY --- PLAYER
        PY --- CSV
        PY --- PNG
        PY --- MQTT
        PY --- NOTIFY
    end

    HA["🏠 Home Assistant<br/>(MQTT Broker)"]

    BE <--> BLE
    BLE <--> PY
    MQTT --> HA

    classDef server fill:#e8f5f4,stroke:#47c2c0,stroke-width:2px
    classDef client fill:#eef3ff,stroke:#5b7cfa,stroke-width:2px
    classDef ble fill:#fff4d6,stroke:#e6a817,stroke-width:2px
    classDef ha fill:#e8e0ff,stroke:#7952b3,stroke-width:2px

    class SERVER,BE,H10,META,TEMP,AIRPODS,KICKR,WATCH,YEELIGHT,AQARA server
    class CLIENT,PY,GRAPHS,GAUGE,PLAYER,CSV,PNG,MQTT,NOTIFY client
    class BLE ble
    class HA ha


---

## 🚀 Быстрый старт

### Требования

**Для эмулятора:**
- Windows 10 (19041+) или Windows 11
- Bluetooth-адаптер с поддержкой **BLE 5.0+** и роли **Peripheral**
  - ✅ Intel AX200/AX210, Realtek RTL8761B
  - ❌ Старые CSR 4.0 адаптеры
- .NET 8 SDK
- Visual Studio 2022

**Для клиента:**
- Python 3.10+
- Bluetooth-адаптер (любой, клиент работает в режиме Central)

### Запуск эмулятора

```bash
cd BleEmulator
```

# 1. Убедитесь, что в BleEmulator.csproj указано:
#    <TargetFramework>net8.0-windows10.0.19041.0</TargetFramework>
#    <Platforms>x64</Platforms>

# 2. Сборка
```
dotnet build -c Debug -p:Platform=x64
```
# 3. Запуск
```
dotnet run
```

# Запуск клиента
```
cd ble_client
```

# 1. Установка зависимостей
```
pip install -r requirements.txt
```

# 2. Запуск
```
python main.py
```

### 🔔 Уведомления Windows

Автоматические toast-уведомления при:
💓 Пульс > 160 bpm или < 40 bpm
🌡️ Температура > 30°C или < 16°C
🔋 Батарея < 20%
🔒 Превышение попыток ввода PIN
Настраиваемые пороги и cooldown (по умолчанию 60 сек).

### 📦 Структура проекта

ble-iot-platform/
├── README.md
├── BleEmulator/                    # C# эмулятор
│   ├── BleEmulator.csproj
│   ├── Program.cs
│   ├── Emulators/
│   │   ├── BaseEmulator.cs
│   │   ├── FitnessTracker.cs
│   │   ├── SmartGlasses.cs
│   │   ├── HomeSensor.cs
│   │   ├── Headphones.cs
│   │   ├── CyclingSensor.cs
│   │   ├── SmartWatch.cs
│   │   ├── SmartBulb.cs
│   │   └── SmartLock.cs
│   └── Presets/                    # Медиа-файлы для очков
│
└── ble_client/                     # Python клиент
    ├── main.py
    ├── requirements.txt
    ├── core/
    │   ├── async_worker.py
    │   ├── ble_manager.py
    │   └── device_registry.py
    ├── ui/
    │   ├── main_window.py
    │   ├── connection_tab.py
    │   ├── services_tab.py
    │   ├── log_panel.py
    │   └── widgets/
    │       ├── real_time_plot.py
    │       ├── gauge_widget.py
    │       └── media_player.py
    ├── devices/
    │   ├── base_device.py
    │   └── [8 файлов устройств]
    ├── services/
    │   ├── data_logger.py          # CSV
    │   ├── chart_exporter.py       # PNG
    │   ├── mqtt_service.py         # MQTT
    │   └── notifier.py             # Уведомления
    └── exports/                    # Создаётся автоматически
        ├── csv/
        └── charts/
