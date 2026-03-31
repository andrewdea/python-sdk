#include "templates.h"

// Instantiate templates
Container<double> doubleContainer(3.14);
Container<int> intContainer(42);
Container<char*> ptrContainer(nullptr);

void useTemplates() {
  auto result1 = add(1, 2);
  auto result2 = add(1.5, 2.5);
}

// Made with Bob
