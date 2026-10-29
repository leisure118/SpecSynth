/*@
  requires n >= 0;
  requires \valid(a + (0 .. n-1));
  assigns \nothing;
  ensures \result == 1 <==> \forall integer j; 0 <= j < n ==> a[j] % 2 == 0;
*/
int areElementsEven(int *a, int n) {
    int p = 0;
    /*@
      loop invariant 0 <= p <= n;
      loop invariant \forall integer j; 0 <= j < p ==> a[j] % 2 == 0;
      loop assigns p;
      loop variant n - p;
    */
    while (p < n) {
        if (a[p] % 2 != 0) {
            return 0;
        }
        p = p + 1;
    }
    return 1;
}
void main() {
    int arr[] = {2,4,6,8,10};
    int res = areElementsEven(arr, 5);
    //@ assert res == 1;
}