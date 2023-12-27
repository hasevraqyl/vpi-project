from Polity import Polity
from Province import Province
from Material import Material
from System import System
from ProvinceResource import ProvinceResource

rossiya = Polity()
rossiya.set_Name("rossiya")
cfo = System()
cfo.set_ReigningPolity(rossiya)
tver = Province()
vologda = Province()
yaroslavl = Province()
tver.set_ReigningSystem(cfo)
yaroslavl.set_ReigningSystem(cfo)
vologda.set_ReigningSystem(cfo)
lyes = Material()
vodka = Material()
lyestver = ProvinceResource()
lyesvologda = ProvinceResource()
vodkayaroslavl = ProvinceResource()
lyestver.set_TurnProduction(15)
lyesvologda.set_TurnProduction(20)
vodkayaroslavl.set_TurnProduction(5)
lyestver.set_Material(lyes)
lyesvologda.set_Material(lyes)
vodkayaroslavl.set_Material(vodka)
lyestver.set_Province(tver)
lyesvologda.set_Province(vologda)
vodkayaroslavl.set_Province(yaroslavl)
tver.set_ResourcesFromProvince([lyestver])
vologda.set_ResourcesFromProvince([lyesvologda])
yaroslavl.set_ResourcesFromProvince([vodkayaroslavl])
rossiya.set_Systems([cfo])
cfo.set_Provinces([tver, yaroslavl, vologda])
rossiya.TurnPassed()
print(
    "this is the number of the first resource:",
    rossiya.get_Resources()[0].get_Quantity(),
    "this is the number of the second resource:",
    rossiya.get_Resources()[1].get_Quantity(),
)
