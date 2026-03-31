#include "function_pointers.h"

namespace TestNamespace {

void callbackFunction(int value) {
  // Callback implementation
}

void anotherCallback(int value) {
  // Another callback implementation
}

void executeCallback(void (*callback)(int), int value) {
  if (callback) {
    callback(value);  // Function pointer call
  }
}

// CallbackHandler implementation
CallbackHandler::CallbackHandler() : callback(nullptr) {}

void CallbackHandler::setCallback(void (*cb)(int)) {
  callback = cb;
}

void CallbackHandler::trigger(int value) {
  if (callback) {
    callback(value);  // Function pointer call through member
  }
}

void (*getCallback(bool useFirst))(int) {
  return useFirst ? callbackFunction : anotherCallback;
}

}  // namespace TestNamespace

// Made with Bob
