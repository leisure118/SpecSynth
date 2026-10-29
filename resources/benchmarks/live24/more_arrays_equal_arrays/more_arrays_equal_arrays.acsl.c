/*@
  requires n >= 0;
  requires \valid(a+(0..n-1));
  requires \valid(b+(0..n-1));
  assigns \nothing;
  ensures \result == 1 <==> \forall integer j; 0 <= j < n ==> a[j] == b[j];
*/
int check(int *a, int *b, int n) {
    /*@
      loop invariant 0 <= i <= n;
      loop invariant \forall integer j; 0 <= j < i ==> a[j] == b[j];
      loop assigns i;
      loop variant n - i;
    */
    for (int i = 0; i < n; i++) {
        if (a[i] != b[i]) {
            return 0;
        }
    }
    return 1;
}
int main() {
    int a[] = {1,2,3,4,5};
    int b[] = {1,2,3,4,5};
    int res = check(a, b, 5);
    //@ assert res == 1;
}