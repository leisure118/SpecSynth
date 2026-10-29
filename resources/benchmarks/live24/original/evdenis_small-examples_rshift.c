unsigned rshift(unsigned a)
{
	return a >> 1;
}
int main(){
	unsigned a = 10;
	unsigned b = rshift(a);
	//@ assert b == 5;
}