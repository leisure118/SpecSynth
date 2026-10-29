/*@
  requires num >= 0;
  ensures \result == 6;
  assigns \nothing;
*/
int func(int num) {
    int i = 0;
    int sum = 0;

    /*@
      loop invariant 0 <= num;
      loop assigns i, sum, num;
      loop variant num;
    */
    while(num>0) {
        i = num%10;
        sum += i;
        num /= 10;
    }
    /*@
      admit sum == 6;
    */
    return sum;
}

// write a test
void main() {
    int t = func(123);
    //@ assert t == 6;
}
