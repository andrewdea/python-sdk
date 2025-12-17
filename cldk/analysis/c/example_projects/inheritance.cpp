#include <iostream>
using namespace std;

class LandVehicle
{
  public:
    void landInfo()
    {
        cout << "This is a LandVehicle" << endl;
    }
};

class WaterVehicle
{
  public:
    void waterInfo()
    {
        cout << "This is a WaterVehicle" << endl;
    }
};

// Derived class inheriting from both base classes
class AmphibiousVehicle : public LandVehicle, public WaterVehicle
{
  public:
    AmphibiousVehicle()
    {
        cout << "This is an AmphibiousVehicle" << endl;
    }
};

int main()
{
    AmphibiousVehicle obj;

    obj.waterInfo();
    obj.landInfo();

    return 0;
}