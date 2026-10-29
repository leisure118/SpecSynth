/*@
  requires n >= 0;
  requires \valid_read(a+(0 .. n-1));
  requires \valid_read(b+(0 .. n-1));
  assigns \nothing;
  ensures (\forall integer j; 0 <= j < n ==> a[j] == b[j]) <==> \result == 1;
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
    int ans = check(a, b, 5);
    //@ assert ans == 1;
}