/*@ axiomatic Factorial {
    logic integer factorial(integer i);
    axiom nil:
       factorial(0) == 1;
    axiom step:
       \forall integer i; i >= 0 ==>
          factorial(i) == factorial(i - 1) * i;
    lemma non_negative:
       \forall integer i; i >= 0 ==>
          factorial(i) > 0;
    }
 */
#define SPEC_ULONG_MAX 18446744073709551615UL
/*@
  assigns \nothing;
  ensures \result == factorial(\old(i));
*/
unsigned long factorial(unsigned i)
{
	unsigned long f = 1;
	/*@
	  loop invariant i <= \at(i, Pre);
	  loop invariant f * factorial(i) == factorial(\at(i, Pre));
	  loop assigns f, i;
	  loop variant i;
	*/
	while (i) {
		f *= i--;
	}
	return f;
}
int main(){
    unsigned long f = factorial(5);
    //@ assert f == 120;
}