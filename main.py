import ifcopenshell.api
import ifcopenshell.util.element
from pathlib import Path
import math

# Пути к файлу IFC
pathIFC = Path(r'D:\12_TeklaStructuresModels\105-2022-09-КР.КМ-TS2022\IFC\out.ifc')

# Путь к параметрам проекта из Revit
pathProjectInfo = Path(r'D:\05_Эксперименты\20230829_IFC_РедактированиеПараметровPython\102-2022-01-АР-REV21_ProjectParams.csv')

# Словари для записи в IFC и маппинга параметров
# Структура:
# "Название параметра в revit": ["Название параметра в IFC", "Тип данных в IFC"]
param_dict = {}
param_mapping = {
    "Номер проекта": ["Шифр проекта", "Text"],
    "Наименование проекта": ["Наименование проекта", "Text"],
    "Адрес проекта": ["Адрес участк", "Text"],
    "Заказчик": ["Заказчик", "Text"],
    "Название организации": ["Проектировщик", "Text"],
    "VKPR_Общая площадь здания": ["Общая площадь здания", "Area"],
    "VKPR_Расчетная площадь здания": ["Расчетная площадь здания", "Area"],
    "VKPR_Строительный объем здания": ["Строительный объем здания", "Volume"],
    "VKPR_Отметка нуля проекта": ["Отметка нуля проекта", "Real"],
    "VKPR_Отметка уровня земли": ["Отметка уровня земли", "Real"],
    "VKPR_Вид строительства": ["Вид строительства", "Text"],
    "VKPR_Номер ГПЗУ": ["Номер ГПЗУ", "Text"]
}

# Открытие модели и получение объектов для обработки
model = ifcopenshell.open(pathIFC)
site = model.by_type("IfcSite")[0]
building = model.by_type('IFCBUILDING')[0]

# Задание угла поворота здания
building_Angle = -45
if site.ObjectPlacement is not None and site.ObjectPlacement.is_a("IfcLocalPlacement"):
    refs = model.get_inverse(site.ObjectPlacement)
    site.ObjectPlacement.RelativePlacement = model.createIfcAxis2Placement3D(
        model.createIfcCartesianPoint((55000., 65000., 195000.)),
        model.createIfcDirection((0., 0., 1.)),
        model.createIfcDirection(
            (math.cos(building_Angle * math.pi / 180),
             math.sin(building_Angle * math.pi / 180),
             0.)
        )
    )
    # назначение положения ссылочны объектам в иерархии
    for ref in refs:
        if ref.is_a("IfcLocalPlacement"): ref.PlacementRelTo = site.ObjectPlacement

# Обработка параметров и приведение к типам IFC - наполнение словаря для записи в IFC
with open(pathProjectInfo, encoding='UTF-8', mode='r') as file:
    lines = file.readlines()
    for line in lines:
        param_value = line.strip().split(':', 1)
        param_value[0] = param_value[0].strip()
        param_value[1] = param_value[1].strip()
        if param_value[0] in param_mapping.keys():
            if param_mapping[param_value[0]][1] == "Text":
                param_value[0] = param_mapping[param_value[0]][0]
                param_dict[param_value[0]] = param_value[1]
            elif param_mapping[param_value[0]][1] == "Real":
                param_value[0] = param_mapping[param_value[0]][0]
                param_dict[param_value[0]] = float(param_value[1].replace(',','.'))
            elif param_mapping[param_value[0]][1] == "Area":
                param_value[0] = param_mapping[param_value[0]][0]
                param_dict[param_value[0]] = model.createIfcAreaMeasure(float(param_value[1].replace(',','.')))
            elif param_mapping[param_value[0]][1] == "Volume":
                param_value[0] = param_mapping[param_value[0]][0]
                param_dict[param_value[0]] = model.createIfcVolumeMeasure(float(param_value[1].replace(',','.')))

# Добавление PSet для объекта IfcBuilding
pset = ifcopenshell.api.run("pset.add_pset", model, product=building, name="Общие параметры здания")

# Редактирование добавленного PSet
for relationship in building.IsDefinedBy:
    if relationship.is_a('IfcRelDefinesByProperties'):
        definition = relationship.RelatingPropertyDefinition
        ifcopenshell.api.run('pset.edit_pset', model, pset=definition, properties=param_dict)

# Запись изменений в модель
model.write(pathIFC)
