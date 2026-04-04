import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useAuth } from '@/lib/hooks/useAuth';
import { Button, Input, Card, CardContent } from '@/components/ui';
import { LoadingSpinner } from '@/components/common';

const registerSchema = z.object({
  name: z.string().min(1, 'Company name is required'),
  slug: z
    .string()
    .min(1, 'Slug is required')
    .regex(/^[a-z0-9-]+$/, 'Only lowercase letters, numbers, and hyphens'),
  admin_email: z.string().email('Invalid email address'),
  admin_password: z.string().min(8, 'Password must be at least 8 characters'),
  confirm_password: z.string().min(1, 'Please confirm your password'),
}).refine((data) => data.admin_password === data.confirm_password, {
  message: "Passwords don't match",
  path: ['confirm_password'],
});

type RegisterForm = z.infer<typeof registerSchema>;

const RegisterPage: React.FC = () => {
  const { registerTenant } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterForm) => {
    setIsLoading(true);
    setError(null);
    try {
      await registerTenant({
        name: data.name,
        slug: data.slug,
        admin_email: data.admin_email,
        admin_password: data.admin_password,
      });
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <Card className="w-full max-w-md">
        <CardContent className="pt-6">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900">AgentAichain</h2>
            <p className="mt-2 text-sm text-gray-600">
              Create your tenant
            </p>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-600">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <Input
              label="Company Name"
              placeholder="Acme Corp"
              error={errors.name?.message}
              {...register('name')}
            />

            <Input
              label="Tenant Slug"
              placeholder="acme-corp"
              error={errors.slug?.message}
              {...register('slug')}
            />
            <p className="text-xs text-gray-500 -mt-2">
              Used in URLs. Only lowercase letters, numbers, and hyphens.
            </p>

            <Input
              label="Admin Email"
              type="email"
              placeholder="admin@acme.com"
              error={errors.admin_email?.message}
              {...register('admin_email')}
            />

            <Input
              label="Password"
              type="password"
              placeholder="••••••••"
              error={errors.admin_password?.message}
              {...register('admin_password')}
            />

            <Input
              label="Confirm Password"
              type="password"
              placeholder="••••••••"
              error={errors.confirm_password?.message}
              {...register('confirm_password')}
            />

            <Button
              type="submit"
              className="w-full"
              size="lg"
              isLoading={isLoading}
            >
              Create Tenant
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Already have an account?{' '}
              <Link
                to="/login"
                className="font-medium text-primary-600 hover:text-primary-500"
              >
                Sign in
              </Link>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default RegisterPage;
