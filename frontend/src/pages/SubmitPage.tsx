import React from 'react';
import { SubmitForm } from '../components/SubmitForm';

export const SubmitPage: React.FC = () => {
  return (
    <div className="py-8">
      <h1 className="text-3xl font-bold text-center text-gray-900 mb-8">File a New Complaint</h1>
      <SubmitForm />
    </div>
  );
};
