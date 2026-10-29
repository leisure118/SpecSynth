/*@
  ensures \result == 1 <==> x > 0;
  ensures \result == -1 <==> x < 0;
  ensures \result == 0 <==> x == 0;
  assigns \nothing;
*/
int spec_sign(int x)
{
   return (x > 0) - (x < 0);
}
int main(void)
{
   int a = spec_sign(10);
   //@ assert a == 1;
   int b = spec_sign(0);
   //@ assert b == 0;
}