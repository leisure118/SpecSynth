#include<stdio.h>
int* reverse(int a[], int n, int b[]) {
	int i = 0;
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