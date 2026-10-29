int max3(int a, int b, int c)
{
	return a > b ? (a > c ? a : c) : (b > c ? b : c);
}
int main(){
	int a = 1;
	int b = 2;
	int c = 3;
	int d = max3(a, b, c);
    //@ assert d == 3;
}