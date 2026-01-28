from aiogram.fsm.state import State, StatesGroup

class RegistrationSG(StatesGroup):
    q1_source = State()
    custom_source_text = State()
    q2_exp = State()

class ChangeTagSG(StatesGroup):
    new_tag = State()

class ManageUserSG(StatesGroup):
    input_user = State()

class CreateLogSG(StatesGroup):
    imei = State()
    model = State()
    worker = State()
    mail = State()

class CreateProfitSG(StatesGroup):
    choose_source = State()
    amount = State()
    worker = State()
    model = State()

class BroadcastSG(StatesGroup):
    input_text = State()
    confirm = State()

class CreateLinkSG(StatesGroup):
    input_name = State()

# 🔥 НОВОЕ СОСТОЯНИЕ
class EditResourceSG(StatesGroup):
    input_link = State()