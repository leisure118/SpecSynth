int main() {
  int s[6] = {104, 101, 108, 108, 111, 0};
  int i = 0;
  while (s[i] != 0) {
    i++;
  }
  //@ assert(i == 5);
  return 0;
}
