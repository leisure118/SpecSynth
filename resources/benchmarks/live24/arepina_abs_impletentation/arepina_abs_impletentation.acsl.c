#define SPEC_INT_MIN -2147483648
#define SPEC_INT_MAX 2147483647
/*@
  assigns \nothing;
  ensures a >= 0 ==> \result == (long)a;
  ensures a < 0 ==> \result == -(long)a;
*/
long spec_abs1(int a)
{
   long abs;
   abs = a;
   if (a < 0) {
      abs = -abs;
   }
   return abs;
}
int main(void)
{
   int a = spec_abs1(SPEC_INT_MIN+1);
   //@ assert a == SPEC_INT_MAX;
}