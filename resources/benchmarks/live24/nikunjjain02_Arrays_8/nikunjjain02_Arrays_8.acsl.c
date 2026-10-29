#include<stdio.h>
/*@
  requires n >= 0;
  requires \valid(a + (0 .. n-1));
  requires \valid(b + (0 .. n-1));
  assigns b[0 .. n-1];
  ensures \result == b;
  ensures \forall integer k; 0 <= k < n ==> \result[k] == a[n-k-1];
*/
int* reverse(int a[], int n, int b[]) {
	int i = 0;
	/*@
	  loop invariant 0 <= i <= n;
	  loop invariant \forall integer j; 0 <= j < i ==> b[j] == a[n-j-1];
	  loop assigns i, b[0 .. n-1];
	  loop variant n - i;
	*/
	while(i<n) {
		b[i]=a[n-i-1];
		i++;
	}
	return b;
}
void main() {
	int a[] = {21, 24, 23, 24, 25};
	int b[10];
	int* c = reverse(a, 5, b);
	//@ assert \forall integer k; 0 <= k < 5 ==> c[k] == a[5-k-1];
}