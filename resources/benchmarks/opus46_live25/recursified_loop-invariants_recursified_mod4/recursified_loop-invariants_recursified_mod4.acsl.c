#include<limits.h>

/*@ lemma mod4_uint32:
  \forall integer n; 0 <= n <= 4294967295 ==>
    n % 4 == 0 ==>
    (n + 4) % 4294967296 % 4 == 0;
*/

/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
/*@
  requires \valid(x);
  requires *x % 4 == 0;
  assigns *x;
  ensures *x % 4 == 0;
*/
void func_to_recursive_line_13_to_14_0(unsigned int *x)
{
  if (unknown())
  {
    {
      //@ ghost unsigned int old_x = *x;
      //@ assert old_x % 4 == 0;
      //@ assert old_x <= 4294967292;
      *x += 4;
      //@ assert old_x < 4294967292 ==> *x == old_x + 4;
      //@ assert old_x == 4294967292 ==> *x == 0;
      //@ assert *x % 4 == 0;
    }
    func_to_recursive_line_13_to_14_0(x);
  }
  else
  {
  }
}
int main(void)
{
  unsigned int x = 0;
  func_to_recursive_line_13_to_14_0(&x);
  //@assert(!(x % 4));
  return 0;
}
