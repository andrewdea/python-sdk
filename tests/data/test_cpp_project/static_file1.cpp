// Test case for static function handling with USR-based identification
// This file contains a static function named 'helper'

#include <iostream>

// Static function in this TU
static void helper() {
  std::cout << "Helper from static_file1.cpp\n";
}

void callHelperFromFile1() {
  helper();  // Should link to the local static helper via USR
}

// Made with Bob
