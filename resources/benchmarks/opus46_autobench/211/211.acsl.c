/*@ logic integer digit_sum(integer n) = n <= 0 ? 0 : n % 10 + digit_sum(n / 10); */

/*@
  requires num >= 0;
  assigns \nothing;
  ensures \result == digit_sum(\old(num));
*/
int func(int num) {
    int i = 0;
    int sum = 0;

    /*@
      loop invariant num >= 0;
      loop invariant sum >= 0;
      loop invariant sum + digit_sum(num) == digit_sum(\at(num, Pre));
      loop assigns num, i, sum;
      loop variant num;
    */
    while(num>0) {
        i = num%10;
        sum += i;
        num /= 10;
    }
    return sum;
}

// write a test
void main() {
    int t = func(123);
    //@ assert t == 6;
}
