unsigned lower_bound_raw(const int *a, unsigned n, int val)
{
   unsigned i = 0;
   for(; i < n; ++i) {
      if (a[i] >= val) {
         break;
      }
   }
   //@ assert \forall integer k; 0 <= k < i ==> a[k] < val;
   return i;
}