#include<stddef.h>
void search_and_replace(int* array, size_t length, int old, int new) {
	for(size_t i = 0;i < length; ++i) {
		if(array[i]==old) array[i]=new;
	}
}
void main() {
	int a[] = {1, 2, 4, 5};
	search_and_replace(a, 4, 2, 3);
	//@ assert a[0] == 1 && a[1] == 3 && a[2] == 4 && a[3] == 5;
}