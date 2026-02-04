import time
import threading
from enum import Enum
from typing import Callable, Optional, List
from dataclasses import dataclass


class DrinkType(Enum):
    """Типы напитков"""
    NONE = 0
    ESPRESSO = 1
    AMERICANO = 2
    CAPPUCCINO = 3
    LATTE = 4
    HOT_WATER = 5
    
    def __str__(self):
        names = {
            0: "Не выбран",
            1: "Эспрессо",
            2: "Американо",
            3: "Капучино",
            4: "Латте",
            5: "Горячая вода"
        }
        return names.get(self.value, "Неизвестно")


class MachineState(Enum):
    """Состояния кофемашины"""
    OFF = 0
    WARMING = 1
    READY = 2
    BUSY = 3
    ERROR = 4
    
    def __str__(self):
        names = {
            0: "Выключена",
            1: "Прогрев",
            2: "Готова",
            3: "Занята",
            4: "Ошибка"
        }
        return names.get(self.value, "Неизвестно")


class BusySubState(Enum):
    """Подсостояния состояния BUSY"""
    WAITING_CUP = 1
    GRINDING = 2
    HEATING = 3
    BREWING = 4
    FROTHING = 5
    DONE = 6
    
    def __str__(self):
        names = {
            1: "Ожидание чашки",
            2: "Помол",
            3: "Нагрев",
            4: "Пролив",
            5: "Взбивание молока",
            6: "Готово"
        }
        return names.get(self.value, "")


class ActuatorState(Enum):
    """Состояния исполнительного устройства"""
    OFF = 0
    ON = 1
    ERROR = 2


class SensorType(Enum):
    """Типы датчиков"""
    WATER_LEVEL = 1
    BEANS = 2
    WASTE = 3
    TEMPERATURE = 4
    OVERHEAT = 5
    CUP = 6


class EventType(Enum):
    """Типы событий"""
    BUTTON_PRESSED = 1
    SENSOR_ALERT = 2
    TIMER_TIMEOUT = 3
    OVERHEAT = 4


class Sensor:
    """Базовый класс датчика"""
    
    def __init__(self, sensor_type: SensorType, name: str, threshold: float = 0):
        self.sensor_type = sensor_type
        self.name = name
        self.threshold = threshold
        self._value: float = 0
    
    def get_value(self) -> float:
        return self._value
    
    def set_value(self, value: float) -> None:
        self._value = value
    
    def is_threshold_exceeded(self) -> bool:
        return self._value >= self.threshold
    
    def __str__(self):
        return f"{self.name}: {self._value}"


class WaterLevelSensor(Sensor):
    """Датчик уровня воды (0-100%)"""
    
    def __init__(self):
        super().__init__(SensorType.WATER_LEVEL, "Датчик воды", threshold=20)
        self._value = 100  # Полный резервуар
    
    def is_enough_water(self) -> bool:
        return self._value >= self.threshold
    
    def consume(self, amount: float) -> None:
        self._value = max(0, self._value - amount)


class BeansSensor(Sensor):
    """Датчик наличия зёрен (0-100%)"""
    
    def __init__(self):
        super().__init__(SensorType.BEANS, "Датчик зёрен", threshold=10)
        self._value = 100
    
    def has_beans(self) -> bool:
        return self._value >= self.threshold
    
    def consume(self, amount: float) -> None:
        self._value = max(0, self._value - amount)


class WasteSensor(Sensor):
    """Датчик заполнения контейнера отходов (0-100%)"""
    
    def __init__(self):
        super().__init__(SensorType.WASTE, "Датчик отходов", threshold=90)
        self._value = 0
    
    def is_full(self) -> bool:
        return self._value >= self.threshold
    
    def add_waste(self, amount: float) -> None:
        self._value = min(100, self._value + amount)
    
    def empty(self) -> None:
        self._value = 0


class TemperatureSensor(Sensor):
    """Датчик температуры воды"""
    
    def __init__(self):
        super().__init__(SensorType.TEMPERATURE, "Датчик температуры", threshold=90)
        self._value = 25  # Комнатная температура
    
    def is_ready(self) -> bool:
        return 90 <= self._value <= 95
    
    def is_overheated(self) -> bool:
        return self._value > 120


class CupSensor(Sensor):
    """Датчик наличия чашки"""
    
    def __init__(self):
        super().__init__(SensorType.CUP, "Датчик чашки")
        self._value = 0  # 0 = нет чашки, 1 = есть
    
    def has_cup(self) -> bool:
        return self._value == 1
    
    def place_cup(self) -> None:
        self._value = 1
    
    def remove_cup(self) -> None:
        self._value = 0


class Actuator:
    """Базовый класс исполнительного устройства"""
    
    def __init__(self, name: str):
        self.name = name
        self.state = ActuatorState.OFF
    
    def turn_on(self) -> bool:
        if self.state != ActuatorState.ERROR:
            self.state = ActuatorState.ON
            return True
        return False
    
    def turn_off(self) -> None:
        if self.state != ActuatorState.ERROR:
            self.state = ActuatorState.OFF
    
    def get_state(self) -> ActuatorState:
        return self.state
    
    def is_on(self) -> bool:
        return self.state == ActuatorState.ON
    
    def __str__(self):
        return f"{self.name}: {self.state.name}"


class Grinder(Actuator):
    """Кофемолка"""
    
    def __init__(self):
        super().__init__("Кофемолка")
        self.grind_time = 7  # секунд
    
    def grind(self, callback: Optional[Callable] = None) -> None:
        """Помол зёрен"""
        self.turn_on()
        # В реальной системе здесь был бы таймер
        if callback:
            callback()
        self.turn_off()


class Pump(Actuator):
    """Помпа для подачи воды"""
    
    def __init__(self):
        super().__init__("Помпа")
        self.pressure = 9  # бар
    
    def set_pressure(self, pressure: float) -> None:
        self.pressure = pressure
    
    def pour(self, callback: Optional[Callable] = None) -> None:
        """Пролив воды"""
        self.turn_on()
        if callback:
            callback()
        self.turn_off()


class Heater(Actuator):
    """Нагревательный элемент"""
    
    def __init__(self, temp_sensor: TemperatureSensor):
        super().__init__("Нагреватель")
        self.temp_sensor = temp_sensor
        self.target_temp = 93
    
    def heat(self) -> None:
        """Нагрев воды"""
        self.turn_on()
        # Симуляция нагрева
        current = self.temp_sensor.get_value()
        if current < self.target_temp:
            self.temp_sensor.set_value(min(current + 10, self.target_temp))
    
    def is_ready(self) -> bool:
        return self.temp_sensor.is_ready()


class Frother(Actuator):
    """Капучинатор (вспениватель молока)"""
    
    def __init__(self):
        super().__init__("Капучинатор")
        self.froth_time = 15  # секунд
    
    def froth(self, callback: Optional[Callable] = None) -> None:
        """Взбивание молока"""
        self.turn_on()
        if callback:
            callback()
        self.turn_off()


class Display:
    """Дисплей кофемашины"""
    
    def __init__(self):
        self.current_message = ""
        self.progress = 0
    
    def show_message(self, message: str) -> None:
        self.current_message = message
        print(f"[ДИСПЛЕЙ] {message}")
    
    def show_progress(self, percent: int) -> None:
        self.progress = percent
        bar = "█" * (percent // 10) + "░" * (10 - percent // 10)
        print(f"[ДИСПЛЕЙ] Прогресс: [{bar}] {percent}%")
    
    def show_error(self, error: str) -> None:
        self.current_message = f"ОШИБКА: {error}"
        print(f"[ДИСПЛЕЙ] ОШИБКА: {error}")
    
    def show_state(self, state: MachineState, drink: DrinkType = DrinkType.NONE) -> None:
        if state == MachineState.READY:
            self.show_message(f"Готова к работе. Выберите напиток.")
        elif state == MachineState.BUSY:
            self.show_message(f"Готовлю: {drink}")
        elif state == MachineState.WARMING:
            self.show_message("Прогрев...")
        elif state == MachineState.OFF:
            self.show_message("Выключена")
        elif state == MachineState.ERROR:
            self.show_message("Ошибка! Требуется обслуживание.")
    
    def clear(self) -> None:
        self.current_message = ""
        self.progress = 0


class Button:
    """Базовый класс кнопки"""
    
    def __init__(self, name: str):
        self.name = name
        self.is_lit = False
        self.is_pressed = False
        self._callback: Optional[Callable] = None
    
    def set_callback(self, callback: Callable) -> None:
        self._callback = callback
    
    def press(self) -> None:
        self.is_pressed = True
        print(f"[КНОПКА] Нажата: {self.name}")
        if self._callback:
            self._callback()
    
    def release(self) -> None:
        self.is_pressed = False
    
    def light_on(self) -> None:
        self.is_lit = True
        print(f"[КНОПКА] {self.name} - подсветка ВКЛ")
    
    def light_off(self) -> None:
        self.is_lit = False
        print(f"[КНОПКА] {self.name} - подсветка ВЫКЛ")


class DrinkButton(Button):
    """Кнопка выбора напитка"""
    
    def __init__(self, drink_type: DrinkType):
        super().__init__(str(drink_type))
        self.drink_type = drink_type


class PowerButton(Button):
    """Кнопка питания"""
    
    def __init__(self):
        super().__init__("Питание")


class CancelButton(Button):
    """Кнопка отмены"""
    
    def __init__(self):
        super().__init__("Отмена")


class Timer:
    """Таймер для отслеживания времени операций"""
    
    def __init__(self):
        self.duration = 0
        self.remaining = 0
        self.is_running = False
        self._callback: Optional[Callable] = None
        self._thread: Optional[threading.Thread] = None
    
    def start(self, duration: float, callback: Optional[Callable] = None) -> None:
        self.duration = duration
        self.remaining = duration
        self.is_running = True
        self._callback = callback
        print(f"[ТАЙМЕР] Запущен на {duration} сек")
    
    def tick(self, elapsed: float = 1) -> bool:
        """Обновление таймера. Возвращает True если истёк."""
        if not self.is_running:
            return False
        
        self.remaining -= elapsed
        if self.remaining <= 0:
            self.remaining = 0
            self.is_running = False
            print(f"[ТАЙМЕР] Истёк!")
            if self._callback:
                self._callback()
            return True
        return False
    
    def stop(self) -> None:
        self.is_running = False
        print(f"[ТАЙМЕР] Остановлен")
    
    def reset(self) -> None:
        self.remaining = self.duration
        self.is_running = False
    
    def get_remaining(self) -> float:
        return self.remaining
    
    def is_expired(self) -> bool:
        return self.remaining <= 0 and not self.is_running


class ServiceCenter:
    """Сервисная служба для обработки аварий"""
    
    def __init__(self):
        self.alerts: List[str] = []
    
    def receive_alert(self, error: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        alert = f"[{timestamp}] {error}"
        self.alerts.append(alert)
        print(f"[СЕРВИС] Получено оповещение: {error}")
    
    def get_alerts(self) -> List[str]:
        return self.alerts.copy()
    
    def clear_alerts(self) -> None:
        self.alerts.clear()


@dataclass
class Event:
    """Событие системы"""
    event_type: EventType
    data: any = None


class Controller:
    """Контроллер кофемашины - центральный компонент системы"""
    
    def __init__(self):
        # Инициализация датчиков
        self.water_sensor = WaterLevelSensor()
        self.beans_sensor = BeansSensor()
        self.waste_sensor = WasteSensor()
        self.temp_sensor = TemperatureSensor()
        self.cup_sensor = CupSensor()
        
        # Инициализация исполнительных устройств
        self.grinder = Grinder()
        self.pump = Pump()
        self.heater = Heater(self.temp_sensor)
        self.frother = Frother()
        
        # Инициализация UI компонентов
        self.display = Display()
        self.power_button = PowerButton()
        self.cancel_button = CancelButton()
        self.drink_buttons = {
            DrinkType.ESPRESSO: DrinkButton(DrinkType.ESPRESSO),
            DrinkType.AMERICANO: DrinkButton(DrinkType.AMERICANO),
            DrinkType.CAPPUCCINO: DrinkButton(DrinkType.CAPPUCCINO),
            DrinkType.LATTE: DrinkButton(DrinkType.LATTE),
            DrinkType.HOT_WATER: DrinkButton(DrinkType.HOT_WATER),
        }
        
        # Таймер и сервис
        self.timer = Timer()
        self.service = ServiceCenter()
        
        # Состояние системы
        self.state = MachineState.OFF
        self.sub_state: Optional[BusySubState] = None
        self.selected_drink = DrinkType.NONE
        self.progress = 0
        
        # Очередь событий
        self.event_queue: List[Event] = []
        
        # Флаг отмены
        self.cancelled = False
        
        # Настройка callbacks кнопок
        self._setup_buttons()
    
    def _setup_buttons(self) -> None:
        """Настройка обработчиков кнопок"""
        self.power_button.set_callback(self._on_power_pressed)
        self.cancel_button.set_callback(self._on_cancel_pressed)
        for drink, button in self.drink_buttons.items():
            button.set_callback(lambda d=drink: self._on_drink_selected(d))
    
    def _on_power_pressed(self) -> None:
        """Обработка нажатия кнопки питания"""
        if self.state == MachineState.OFF:
            self.power_on()
        else:
            self.power_off()
    
    def _on_cancel_pressed(self) -> None:
        """Обработка нажатия кнопки отмены"""
        if self.state == MachineState.BUSY:
            self.cancelled = True
            self.display.show_message("Отменено пользователем")
    
    def _on_drink_selected(self, drink: DrinkType) -> None:
        """Обработка выбора напитка"""
        if self.state == MachineState.READY:
            self.selected_drink = drink
            self.drink_buttons[drink].light_on()
            self.event_queue.append(Event(EventType.BUTTON_PRESSED, drink))
    
    # Операции управления питанием
    
    def power_on(self) -> bool:
        """Включение кофемашины"""
        if self.state != MachineState.OFF:
            return False
        
        print("\n" + "="*60)
        print("          ВКЛЮЧЕНИЕ КОФЕМАШИНЫ")
        print("="*60)
        
        self.state = MachineState.WARMING
        self.display.show_state(self.state)
        
        # Прогрев
        self._warm_up()
        
        return True
    
    def _warm_up(self) -> None:
        """Прогрев кофемашины"""
        print("\n[СИСТЕМА] Начинаю прогрев...")
        
        steps = 7
        for i in range(steps):
            if self.cancelled:
                break
            self.heater.heat()
            self.display.show_progress((i + 1) * 100 // steps)
            time.sleep(0.3)  # Симуляция времени
        
        if self.temp_sensor.is_ready():
            self.state = MachineState.READY
            self.display.show_state(self.state)
            print("[СИСТЕМА] Кофемашина готова к работе!")
        else:
            self._handle_error("Не удалось достичь рабочей температуры")
    
    def power_off(self) -> None:
        """Выключение кофемашины"""
        print("\n" + "="*60)
        print("          ВЫКЛЮЧЕНИЕ КОФЕМАШИНЫ")
        print("="*60)
        
        # Выключаем все устройства
        self.grinder.turn_off()
        self.pump.turn_off()
        self.heater.turn_off()
        self.frother.turn_off()
        
        # Гасим все кнопки
        for button in self.drink_buttons.values():
            button.light_off()
        
        self.state = MachineState.OFF
        self.selected_drink = DrinkType.NONE
        self.display.show_state(self.state)
        self.temp_sensor.set_value(25)  # Остывание
    
    # Проверки ресурсов
    
    def check_resources(self) -> tuple[bool, str]:
        """Проверка наличия ресурсов"""
        if not self.water_sensor.is_enough_water():
            return False, "Недостаточно воды"
        if not self.beans_sensor.has_beans():
            return False, "Недостаточно зёрен"
        if self.waste_sensor.is_full():
            return False, "Контейнер отходов полон"
        return True, "OK"
    
    def check_cup(self) -> bool:
        """Проверка наличия чашки"""
        return self.cup_sensor.has_cup()
    
    # Приготовление напитков
    
    def select_drink(self, drink: DrinkType) -> bool:
        """Выбор напитка для приготовления"""
        if self.state != MachineState.READY:
            self.display.show_error("Машина не готова")
            return False
        
        self.selected_drink = drink
        self.drink_buttons[drink].light_on()
        return True
    
    def brew(self) -> bool:
        """Приготовление выбранного напитка"""
        if self.state != MachineState.READY:
            return False
        
        if self.selected_drink == DrinkType.NONE:
            self.display.show_error("Выберите напиток")
            return False
        
        # Проверка ресурсов
        ok, msg = self.check_resources()
        if not ok:
            self._handle_error(msg)
            return False
        
        print("\n" + "-"*60)
        print(f"  Приготовление: {self.selected_drink}")
        print("-"*60)
        
        self.state = MachineState.BUSY
        self.cancelled = False
        self.progress = 0
        
        # Выбор алгоритма приготовления
        if self.selected_drink == DrinkType.HOT_WATER:
            success = self._brew_hot_water()
        elif self.selected_drink in [DrinkType.ESPRESSO, DrinkType.AMERICANO]:
            success = self._brew_espresso_based()
        else:  # Капучино, Латте
            success = self._brew_milk_based()
        
        # Завершение
        self._finish_brewing(success)
        return success
    
    def _brew_hot_water(self) -> bool:
        """Приготовление горячей воды"""
        # Проверка чашки
        if not self._wait_for_cup():
            return False
        
        # Пролив
        self._update_progress(BusySubState.BREWING, 50)
        self.pump.turn_on()
        time.sleep(0.5)
        self.pump.turn_off()
        self.water_sensor.consume(15)
        
        self._update_progress(BusySubState.DONE, 100)
        return True
    
    def _brew_espresso_based(self) -> bool:
        """Приготовление эспрессо или американо"""
        # Проверка чашки
        if not self._wait_for_cup():
            return False
        
        # Помол
        self._update_progress(BusySubState.GRINDING, 20)
        self.grinder.turn_on()
        time.sleep(0.5)
        self.grinder.turn_off()
        self.beans_sensor.consume(5)
        self.waste_sensor.add_waste(5)
        
        if self.cancelled:
            return False
        
        # Проверка температуры
        if not self.temp_sensor.is_ready():
            self._update_progress(BusySubState.HEATING, 40)
            while not self.temp_sensor.is_ready() and not self.cancelled:
                self.heater.heat()
                time.sleep(0.2)
        
        if self.cancelled:
            return False
        
        # Пролив
        self._update_progress(BusySubState.BREWING, 70)
        self.pump.turn_on()
        time.sleep(0.5)
        self.pump.turn_off()
        
        water_amount = 30 if self.selected_drink == DrinkType.ESPRESSO else 60
        self.water_sensor.consume(water_amount)
        
        self._update_progress(BusySubState.DONE, 100)
        return True
    
    def _brew_milk_based(self) -> bool:
        """Приготовление напитка с молоком (капучино, латте)"""
        # Сначала эспрессо
        if not self._brew_espresso_based():
            return False
        
        if self.cancelled:
            return False
        
        # Взбивание молока
        self._update_progress(BusySubState.FROTHING, 85)
        self.frother.turn_on()
        time.sleep(0.5)
        self.frother.turn_off()
        
        self._update_progress(BusySubState.DONE, 100)
        return True
    
    def _wait_for_cup(self) -> bool:
        """Ожидание установки чашки"""
        self._update_progress(BusySubState.WAITING_CUP, 5)
        
        if self.check_cup():
            return True
        
        self.display.show_message("Установите чашку")
        
        # Ожидание с таймаутом
        timeout = 10  # секунд
        elapsed = 0
        while elapsed < timeout:
            if self.cancelled:
                return False
            if self.check_cup():
                self.display.show_message("Чашка установлена")
                return True
            time.sleep(0.5)
            elapsed += 0.5
        
        self.display.show_error("Таймаут ожидания чашки")
        return False
    
    def _update_progress(self, sub_state: BusySubState, percent: int) -> None:
        """Обновление прогресса"""
        self.sub_state = sub_state
        self.progress = percent
        self.display.show_message(f"{sub_state}")
        self.display.show_progress(percent)
    
    def _finish_brewing(self, success: bool) -> None:
        """Завершение приготовления"""
        # Выключаем все устройства
        self.grinder.turn_off()
        self.pump.turn_off()
        self.frother.turn_off()
        
        # Гасим подсветку кнопки
        if self.selected_drink in self.drink_buttons:
            self.drink_buttons[self.selected_drink].light_off()
        
        if success and not self.cancelled:
            print("\n" + "="*60)
            print(f"  {self.selected_drink} ГОТОВ!")
            print("="*60 + "\n")
            self.display.show_message(f"{self.selected_drink} готов! Приятного аппетита!")
        elif self.cancelled:
            print("\n[СИСТЕМА] Приготовление отменено")
        
        # Возврат в состояние Ready
        self.state = MachineState.READY
        self.selected_drink = DrinkType.NONE
        self.sub_state = None
        self.progress = 0
        self.cancelled = False
    
    def _handle_error(self, error: str) -> None:
        """Обработка ошибки"""
        self.state = MachineState.ERROR
        self.display.show_error(error)
        self.service.receive_alert(error)
        
        # Выключаем все устройства
        self.grinder.turn_off()
        self.pump.turn_off()
        self.heater.turn_off()
        self.frother.turn_off()
    
    def clear_error(self) -> None:
        """Сброс ошибки"""
        if self.state == MachineState.ERROR:
            self.state = MachineState.READY
            self.display.show_state(self.state)
    
    # ---- Получение состояния ----
    
    def get_state(self) -> MachineState:
        return self.state
    
    def get_status(self) -> dict:
        """Получение полного статуса машины"""
        return {
            "state": str(self.state),
            "sub_state": str(self.sub_state) if self.sub_state else None,
            "selected_drink": str(self.selected_drink),
            "progress": self.progress,
            "water_level": self.water_sensor.get_value(),
            "beans_level": self.beans_sensor.get_value(),
            "waste_level": self.waste_sensor.get_value(),
            "temperature": self.temp_sensor.get_value(),
            "cup_present": self.cup_sensor.has_cup(),
        }
    
    def print_status(self) -> None:
        """Вывод статуса машины"""
        status = self.get_status()
        print("\n" + "="*40)
        print("       СТАТУС КОФЕМАШИНЫ")
        print("="*40)
        print(f"  Состояние:     {status['state']}")
        if status['sub_state']:
            print(f"  Подсостояние:  {status['sub_state']}")
        print(f"  Напиток:       {status['selected_drink']}")
        print(f"  Прогресс:      {status['progress']}%")
        print("-"*40)
        print(f"  Вода:       {status['water_level']:.0f}%")
        print(f"  Зёрна:      {status['beans_level']:.0f}%")
        print(f"  Отходы:     {status['waste_level']:.0f}%")
        print(f"  Температура: {status['temperature']:.0f}°C")
        print(f"  Чашка:      {'Есть' if status['cup_present'] else 'Нет'}")
        print("="*40 + "\n")


class CoffeeMachine:
    def __init__(self):
        self.controller = Controller()
    
    def power_on(self) -> None:
        """Включить кофемашину"""
        self.controller.power_on()
    
    def power_off(self) -> None:
        """Выключить кофемашину"""
        self.controller.power_off()
    
    def make_espresso(self) -> bool:
        """Приготовить эспрессо"""
        self.controller.select_drink(DrinkType.ESPRESSO)
        return self.controller.brew()
    
    def make_americano(self) -> bool:
        """Приготовить американо"""
        self.controller.select_drink(DrinkType.AMERICANO)
        return self.controller.brew()
    
    def make_cappuccino(self) -> bool:
        """Приготовить капучино"""
        self.controller.select_drink(DrinkType.CAPPUCCINO)
        return self.controller.brew()
    
    def make_latte(self) -> bool:
        """Приготовить латте"""
        self.controller.select_drink(DrinkType.LATTE)
        return self.controller.brew()
    
    def make_hot_water(self) -> bool:
        """Налить горячую воду"""
        self.controller.select_drink(DrinkType.HOT_WATER)
        return self.controller.brew()
    
    def place_cup(self) -> None:
        """Установить чашку"""
        self.controller.cup_sensor.place_cup()
        print("[ПОЛЬЗОВАТЕЛЬ] Чашка установлена")
    
    def remove_cup(self) -> None:
        """Убрать чашку"""
        self.controller.cup_sensor.remove_cup()
        print("[ПОЛЬЗОВАТЕЛЬ] Чашка убрана")
    
    def refill_water(self) -> None:
        """Долить воду"""
        self.controller.water_sensor.set_value(100)
        print("[ОБСЛУЖИВАНИЕ] Вода долита")
    
    def refill_beans(self) -> None:
        """Добавить зёрна"""
        self.controller.beans_sensor.set_value(100)
        print("[ОБСЛУЖИВАНИЕ] Зёрна добавлены")
    
    def empty_waste(self) -> None:
        """Очистить контейнер отходов"""
        self.controller.waste_sensor.empty()
        print("[ОБСЛУЖИВАНИЕ] Контейнер отходов очищен")
    
    def status(self) -> None:
        """Показать статус"""
        self.controller.print_status()
    
    def cancel(self) -> None:
        """Отменить приготовление"""
        self.controller.cancel_button.press()


def demo():
    """Демонстрация работы системы кофемашины"""
    
    print("\n" + "="*60)
    print("    ДЕМОНСТРАЦИЯ СРВ «КОФЕМАШИНА»")
    print("="*60)
    
    # Создание кофемашины
    machine = CoffeeMachine()
    
    # Показываем начальный статус
    print("\n1. Начальное состояние:")
    machine.status()
    
    # Включаем машину
    print("\n2. Включение кофемашины:")
    machine.power_on()
    
    # Показываем статус после прогрева
    print("\n3. Статус после прогрева:")
    machine.status()
    
    # Устанавливаем чашку
    print("\n4. Установка чашки:")
    machine.place_cup()
    
    # Готовим эспрессо
    print("\n5. Приготовление эспрессо:")
    machine.make_espresso()
    
    # Убираем чашку и ставим новую
    print("\n6. Меняем чашку:")
    machine.remove_cup()
    machine.place_cup()
    
    # Готовим капучино
    print("\n7. Приготовление капучино:")
    machine.make_cappuccino()
    
    # Финальный статус
    print("\n8. Финальный статус:")
    machine.status()
    
    # Выключаем
    print("\n9. Выключение:")
    machine.power_off()
    
    print("\n" + "="*60)
    print("    ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
    print("="*60 + "\n")


def interactive_demo():
    """Интерактивная демонстрация"""
    
    print("\n" + "="*60)
    print("    ИНТЕРАКТИВНЫЙ РЕЖИМ СРВ «КОФЕМАШИНА»")
    print("="*60)
    
    machine = CoffeeMachine()
    
    commands = {
        "1": ("Включить", machine.power_on),
        "2": ("Выключить", machine.power_off),
        "3": ("Поставить чашку", machine.place_cup),
        "4": ("Убрать чашку", machine.remove_cup),
        "5": ("Эспрессо", machine.make_espresso),
        "6": ("Американо", machine.make_americano),
        "7": ("Капучино", machine.make_cappuccino),
        "8": ("Латте", machine.make_latte),
        "9": ("Горячая вода", machine.make_hot_water),
        "s": ("Статус", machine.status),
        "w": ("Долить воду", machine.refill_water),
        "b": ("Добавить зёрна", machine.refill_beans),
        "e": ("Очистить отходы", machine.empty_waste),
        "q": ("Выход", None),
    }
    
    print("\nКоманды:")
    for key, (name, _) in commands.items():
        print(f"  {key} - {name}")
    
    while True:
        try:
            cmd = input("\nВведите команду: ").strip().lower()
            
            if cmd == "q":
                print("До свидания!")
                break
            
            if cmd in commands:
                name, func = commands[cmd]
                if func:
                    func()
            else:
                print("Неизвестная команда")
                
        except KeyboardInterrupt:
            print("\nПрервано пользователем")
            break
        except EOFError:
            break


if __name__ == "__main__":
    # demo()
    interactive_demo()
