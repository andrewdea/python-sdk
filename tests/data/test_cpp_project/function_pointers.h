#pragma once

namespace TestNamespace {

// Function pointer testing
void callbackFunction(int value);
void anotherCallback(int value);

// Function that takes function pointer
void executeCallback(void (*callback)(int), int value);

// Class with function pointer member
class CallbackHandler {
 public:
  CallbackHandler();
  void setCallback(void (*cb)(int));
  void trigger(int value);

 private:
  void (*callback)(int);
};

// Function returning function pointer
void (*getCallback(bool useFirst))(int);

}  // namespace TestNamespace

// Made with Bob
