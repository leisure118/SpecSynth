/*@ requires n >= 0;
    requires \valid(a + (0..n-1));
    assigns \nothing;
    behavior empty:
      assumes n == 0;
      ensures \result == 0;
    behavior not_empty:
      assumes 0 < n;
      ensures 0 <= \result < n;
      ensures \forall integer i; 0 <= i < n ==> a[i] <= a[\result];
      ensures \forall integer i; 0 <= i < \result ==> a[i] < a[\result];
    complete behaviors;
    disjoint behaviors;
*/
int max_element(int* a, int n)
{
   if (n == 0) {
      return 0;
   }
   int max = 0;
   /*@
       loop invariant 0 <= i <= n;
       loop invariant 0 <= max < n;
       loop invariant \forall integer k; 0 <= k < i ==> a[k] <= a[max];
       loop invariant \forall integer k; 0 <= k < max ==> a[k] < a[max];
       loop assigns max, i;
       loop variant n-i;
   */
   for (int i = 1; i < n; i++) {
      if (a[max] < a[i]) {
         max = i;
      }
   }
   return max;
}
int max_seq(int* p, int n)
{
   return p[max_element(p, n)];
}
int main()
{
   int a[] = {1, 2, 3, 4, 5};
   int n = 5;
   int max_value = max_seq(a, n);
   //@ assert max_value == 5;
}