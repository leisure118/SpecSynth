#include <stddef.h>
int* search(int* array, size_t length, int element) {
	for(size_t i = 0; i < length; i++) 
		if(array[i]==element) return &array[i];
	return NULL;
}
void main() {
	int a[] = {1, 5, 6, 7};
	int* res = search(a, 4, 5);
}