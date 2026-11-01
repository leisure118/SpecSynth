/*@
  requires n == 0 || \valid_read(a + (0 .. n-1));
  assigns \nothing;
  ensures 0 <= \result <= n;
  ensures \forall integer k; 0 <= k < \result ==> a[k] < val;
*/
unsigned lower_bound_raw(const int *a, unsigned n, int val)
{
   unsigned i = 0;
   /*@
     loop invariant 0 <= i <= n;
     loop invariant \forall integer k; 0 <= k < i ==> a[k] < val;
     loop assigns i;
     loop variant n - i;
   */
   for(; i < n; ++i) {
      if (a[i] >= val) {
         break;
      }
   }
   //@ assert \forall integer k; 0 <= k < i ==> a[k] < val;
   return i;
}
