/*@
  requires b != 0;
  ensures \result == a / b;
  assigns \nothing;
*/
int divide(int a, int b)
{
	return a / b;
}
int main(){
	int a = 10;
    int b = 2;
    int c = divide(a, b);
    //@ assert c == 5;
}