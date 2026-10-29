int my_mod(int a, int b){
	int c = a * a;
	int d = c * 3;
	return d % b;
}

void main(){
	int x1 = 5;
	int x2 = 10;
	int y1 = my_mod(x1, 2);
	int y2 = my_mod(x2, 2);
	//@ assert y1 != y2;
}